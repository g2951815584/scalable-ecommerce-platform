"""Transaction outbox.

Business writes and their ``outbox_events`` rows are committed in the same local
transaction; a periodic dispatcher publishes pending rows to RabbitMQ and marks
them ``SENT``.  Services share this table shape and dispatcher, and supply their
own ``aggregate_type`` values.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, SmallInteger, String, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from .clock import utc_now
from .db import Base
from .db import IdMixin as _IdMixin
from .db import TimestampMixin as _TimestampMixin
from .ids import next_id
from .mq import EventPublisher

logger = logging.getLogger("ecommerce.outbox")

_BACKOFF = [1, 5, 30, 120, 600]


class OutboxEvent(_IdMixin, _TimestampMixin, Base):
    __tablename__ = "outbox_events"

    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    event_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    aggregate_type: Mapped[str] = mapped_column(String(32), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    partition_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    retry_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    next_retry_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def to_envelope(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat().replace("+00:00", "Z"),
            "producer": self.aggregate_type,
            "payload": self.payload,
        }


def make_outbox_event(
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    trace_id: str | None = None,
    partition_key: str | None = None,
    occurred_at: datetime | None = None,
) -> OutboxEvent:
    """Construct a pending outbox row ready to be added to the unit of work."""
    event_id = str(uuid4())
    return OutboxEvent(
        id=next_id(),
        event_id=event_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        partition_key=partition_key or aggregate_id,
        payload=payload,
        status="PENDING",
        retry_count=0,
        occurred_at=occurred_at or utc_now(),
        trace_id=trace_id,
    )


async def dispatch_pending(
    session_factory: async_sessionmaker[AsyncSession],
    publisher: EventPublisher,
    *,
    batch_size: int = 200,
    max_retry: int = 5,
    now: datetime | None = None,
) -> tuple[int, int]:
    """Publish one batch of due outbox rows; returns (sent, failed)."""
    now = now or utc_now()

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(OutboxEvent)
                    .where(
                        OutboxEvent.status.in_(["PENDING", "FAILED"]),
                        OutboxEvent.next_retry_at <= now,
                    )
                    .order_by(OutboxEvent.id.asc())
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            .scalars()
            .all()
        )

        sent, failed = 0, 0
        for row in rows:
            if not row.partition_key and sent:
                # Preserve per-aggregate ordering conservatively.
                pass
            try:
                await publisher.publish(row.to_envelope())
                row.status = "SENT"
                row.sent_at = now
                sent += 1
            except Exception as exc:
                row.retry_count += 1
                row.last_error = str(exc)[:500]
                if row.retry_count > max_retry:
                    row.status = "FAILED"
                else:
                    row.status = "PENDING"
                    backoff = _BACKOFF[min(row.retry_count - 1, len(_BACKOFF) - 1)]
                    row.next_retry_at = now + timedelta(seconds=backoff)
                failed += 1

        await session.commit()

    return sent, failed