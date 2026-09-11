"""APScheduler wiring: outbox dispatch and expiry release."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.clock import utc_now
from common.outbox import dispatch_pending
from sqlalchemy import select

logger = logging.getLogger("catalog-service.tasks")


def build_scheduler(session_factory, publisher) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def outbox_job() -> None:
        if publisher is None:
            return
        try:
            sent, failed = await dispatch_pending(session_factory, publisher)
            if sent or failed:
                logger.info("outbox dispatched", extra={"sent": sent, "failed": failed})
        except Exception:
            logger.exception("outbox dispatch failed")

    async def release_expired_job() -> None:
        from app.models.inventory import StockReservation
        from app.services import inventory_service

        async with session_factory() as session:
            rows = list((await session.execute(
                select(StockReservation)
                .where(StockReservation.status == "RESERVED",
                       StockReservation.expires_at < utc_now())
                .limit(200)
            )).scalars().all())
            for row in rows:
                try:
                    await inventory_service.release(
                        session, order_no=row.order_no,
                        items=[{"sku_id": str(row.sku_id), "quantity": row.quantity}],
                        reason="ORDER_TIMEOUT", expired=True)
                except Exception:
                    logger.warning("expired release failed", extra={"order_no": row.order_no})

    scheduler.add_job(outbox_job, "interval", seconds=5, id="outbox_dispatch")
    scheduler.add_job(release_expired_job, "interval", seconds=60, id="release_expired")
    return scheduler