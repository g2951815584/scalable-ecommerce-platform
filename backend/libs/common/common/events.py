"""Versioned event envelope and standard event catalogue."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

PayloadT = TypeVar("PayloadT", bound=dict[str, Any])


class EventType(StrEnum):
    USER_REGISTERED = "user.registered"
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_SHIPPED = "order.shipped"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    STOCK_LOW = "stock.low"


class EventEnvelope(BaseModel, Generic[PayloadT]):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType | str
    event_version: str = "1.0"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    producer: str
    trace_id: str
    payload: PayloadT


def new_event(event_type: EventType | str, producer: str, payload: PayloadT, trace_id: str) -> EventEnvelope[PayloadT]:
    return EventEnvelope(event_type=event_type, producer=producer, payload=payload, trace_id=trace_id)


class InMemoryOutbox:
    """Tiny adapter used by smoke tests; production swaps in a DB outbox."""

    def __init__(self) -> None:
        self.events: list[EventEnvelope[dict[str, Any]]] = []

    async def append(self, event: EventEnvelope[dict[str, Any]]) -> None:
        self.events.append(event)
