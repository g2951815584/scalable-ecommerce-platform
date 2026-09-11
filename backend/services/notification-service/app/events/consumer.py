"""Event consumers: route every subscribed domain event to the dispatcher."""

import logging

logger = logging.getLogger("notification-service.events")

SUBSCRIBED_EVENTS = [
    "user.registered", "order.created", "order.paid", "order.cancelled",
    "order.shipped", "payment.failed", "payment.refunded", "stock.low",
]


async def handle_event(session_factory, settings, envelope: dict) -> None:
    from app.services import notification_service

    await notification_service.dispatch_event(session_factory, envelope, settings)