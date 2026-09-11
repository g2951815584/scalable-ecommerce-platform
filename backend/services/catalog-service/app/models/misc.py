"""Review, reply, tag and change-log models."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class Review(IdMixin, TimestampMixin, Base):
    __tablename__ = "reviews"

    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PUBLISHED")
    hidden_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sku_spec_text: Mapped[str] = mapped_column(String(255), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewReply(IdMixin, TimestampMixin, Base):
    __tablename__ = "review_replies"

    review_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reply_type: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    images: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class Tag(IdMixin, TimestampMixin, Base):
    __tablename__ = "tags"

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(32), nullable=False)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProductTagRel(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_tag_rel"

    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tag_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)


class ProductChangeLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_change_logs"

    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spu_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    before_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    operator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class LowStockAlert(IdMixin, TimestampMixin, Base):
    __tablename__ = "low_stock_alerts"

    sku_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    available: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)