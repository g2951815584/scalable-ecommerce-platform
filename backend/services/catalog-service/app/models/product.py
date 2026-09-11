"""Category (tree) and product aggregate models."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Category(IdMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    depth: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    level_name: Mapped[str] = mapped_column(String(16), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    icon_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    product_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Spu(IdMixin, TimestampMixin, Base):
    __tablename__ = "spus"

    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    min_price_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    max_price_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    sales_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_avg: Mapped[float] = mapped_column(nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    off_sale_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Sku(IdMixin, TimestampMixin, Base):
    __tablename__ = "skus"

    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_code: Mapped[str] = mapped_column(String(64), nullable=False)
    spec_text: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_price_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ENABLED")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductImage(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_images"

    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    image_type: Mapped[str] = mapped_column(String(32), nullable=False, default="GALLERY")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProductAttribute(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_attributes"

    spu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    attr_name: Mapped[str] = mapped_column(String(64), nullable=False)
    attr_value: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)