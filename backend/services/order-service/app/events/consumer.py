"""Event consumers for payment results."""

from __future__ import annotations

import logging

logger = logging.getLogger("order-service.events")


async def handle_payment_succeeded(session_factory, envelope: dict) -> None:
    from app.services import order_service

    if envelope.get("event_type") != "payment.succeeded":
        return
    payload = envelope.get("payload") or {}
    async with session_factory() as session:
        await order_service.handle_payment_succeeded(
            session,
            payment_no=str(payload.get("payment_no")),
            order_no=str(payload.get("order_no")),
            amount_cents=int(payload.get("amount_cents", 0)),
            paid_at=str(payload.get("paid_at", "")),
        )


async def handle_payment_failed(session_factory, envelope: dict) -> None:
    # Status unchanged: only logged; keep the order PENDING_PAYMENT.
    pass