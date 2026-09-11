"""Order aggregate, items, status log and shipping snapshot models."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

ORDER_STATUSES = (
    "PENDING_PAYMENT", "CLOSING", "PAID", "SHIPPED", "RECEIVED",
    "COMPLETED", "CANCELLED", "CLOSED", "REFUNDING", "REFUNDED",
)
FINAL_STATUSES = {"COMPLETED", "CANCELLED", "CLOSED", "REFUNDED"}


class Order(IdMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    order_no: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING_PAYMENT")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    goods_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    shipping_fee_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    discount_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    adjust_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    payable_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    paid_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    refunded_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    item_kind_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status_before_refund: Mapped[str | None] = mapped_column(String(32), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    price_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="WEB")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closing_release_dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stock_released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stock_deduct_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_anomalous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class OrderItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_no: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spu_title: Mapped[str] = mapped_column(String(255), nullable=False)
    sku_spec_text: Mapped[str] = mapped_column(String(255), nullable=False)
    sku_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    unit_price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    item_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)


class OrderStatusLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "order_status_logs"

    order_no: Mapped[str] = mapped_column(String(24), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    operator_type: Mapped[str] = mapped_column(String(16), nullable=False, default="SYSTEM")
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class OrderShippingSnapshot(IdMixin, TimestampMixin, Base):
    __tablename__ = "order_shipping_snapshots"

    order_no: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    address_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    receiver_name: Mapped[str] = mapped_column(String(64), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    province: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    detail_address: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    address_text: Mapped[str] = mapped_column(String(512), nullable=False)


class RefundRequest(IdMixin, TimestampMixin, Base):
    __tablename__ = "refund_requests"

    refund_request_no: Mapped[str] = mapped_column(String(24), nullable=False)
    order_no: Mapped[str] = mapped_column(String(24), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    refund_type: Mapped[str] = mapped_column(String(16), nullable=False, default="FULL")
    refund_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    reason_code: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_desc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)