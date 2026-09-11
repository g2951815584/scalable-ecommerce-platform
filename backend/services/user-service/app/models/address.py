"""Shipping addresses owned by a user."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class UserAddress(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_addresses"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(64), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    province: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    detail_address: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)