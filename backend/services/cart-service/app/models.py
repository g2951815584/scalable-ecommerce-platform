"""Cart persistent models (Redis is the runtime source of truth)."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Cart(IdMixin, TimestampMixin, Base):
    __tablename__ = "carts"

    owner_key: Mapped[str] = mapped_column(String(96), nullable=False)
    owner_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    selected_item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    selected_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    op_seq: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CartItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    snapshot_title: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    snapshot_spec_name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    snapshot_image_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    snapshot_unit_price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)