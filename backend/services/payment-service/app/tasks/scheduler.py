"""APScheduler wiring: outbox dispatch job."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from common.outbox import dispatch_pending

logger = logging.getLogger("payment-service.tasks")


def build_scheduler(session_factory, publisher) -> AsyncIOScheduler:
    """Build the payment-service scheduler. ``publisher`` may be None when
    RabbitMQ is unavailable; the outbox job tolerates that and relies on retries."""
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

    scheduler.add_job(outbox_job, "interval", seconds=5, id="outbox_dispatch")
    return scheduler