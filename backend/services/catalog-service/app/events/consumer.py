"""Event consumers: order.paid (confirm stock) and order.cancelled (release stock)."""

from __future__ import annotations

import logging

logger = logging.getLogger("catalog-service.events")


def _payload(envelope: dict) -> tuple[str, list[dict], str]:
    payload = envelope.get("payload") or {}
    items = [{"sku_id": str(i["sku_id"]), "quantity": i["quantity"]} for i in payload.get("items", [])]
    return str(payload.get("order_no")), items, str(envelope.get("event_id"))


async def handle_order_paid(session_factory, envelope: dict) -> None:
    from app.services import inventory_service

    if envelope.get("event_type") != "order.paid":
        return
    order_no, items, event_id = _payload(envelope)
    if not items:
        return
    async with session_factory() as session:
        await inventory_service.confirm(session, order_no=order_no, items=items, event_id=event_id)


async def handle_order_cancelled(session_factory, envelope: dict) -> None:
    from app.services import inventory_service

    if envelope.get("event_type") != "order.cancelled":
        return
    order_no, items, _ = _payload(envelope)
    async with session_factory() as session:
        await inventory_service.release(
            session, order_no=order_no, items=items or None,
            reason=envelope.get("payload", {}).get("reason", "ORDER_CANCELLED"),
        )