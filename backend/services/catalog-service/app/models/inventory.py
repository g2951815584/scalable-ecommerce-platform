"""Inventory, transaction ledger and stock reservation models."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Inventory(IdMixin, TimestampMixin, Base):
    __tablename__ = "inventories"

    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def available(self) -> int:
        return self.stock - self.reserved


class InventoryTransaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "inventory_transactions"

    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    txn_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False)
    available_after: Mapped[int] = mapped_column(Integer, nullable=False)
    sold_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_type: Mapped[str] = mapped_column(String(16), nullable=False, default="SYSTEM")
    ref_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class StockReservation(IdMixin, TimestampMixin, Base):
    __tablename__ = "stock_reservations"

    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RESERVED")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)