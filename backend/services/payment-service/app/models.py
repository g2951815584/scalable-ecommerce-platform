"""Payment, refund, transaction and callback-log models."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class Payment(IdMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    payment_no: Mapped[str] = mapped_column(String(32), nullable=False)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    refunded_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    third_party_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channel_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Refund(IdMixin, TimestampMixin, Base):
    __tablename__ = "refunds"

    refund_no: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_no: Mapped[str] = mapped_column(String(32), nullable=False)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    refund_type: Mapped[str] = mapped_column(String(16), nullable=False, default="FULL")
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    payment_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    operator_type: Mapped[str] = mapped_column(String(16), nullable=False, default="USER")
    third_party_refund_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PaymentTransaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "payment_transactions"

    transaction_no: Mapped[str] = mapped_column(String(32), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(16), nullable=False)
    payment_no: Mapped[str] = mapped_column(String(32), nullable=False)
    refund_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="SUCCEEDED")
    third_party_transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaymentCallbackLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "payment_callback_logs"

    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    third_party_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_body: Mapped[str] = mapped_column(String(65536), nullable=False)
    verify_result: Mapped[str] = mapped_column(String(16), nullable=False, default="PASS")
    process_result: Mapped[str] = mapped_column(String(32), nullable=False, default="RECEIVED")
    process_note: Mapped[str | None] = mapped_column(String(255), nullable=True)