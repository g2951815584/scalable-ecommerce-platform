"""Pydantic contracts for catalog-service."""
from pydantic import BaseModel, Field


class ReserveItem(BaseModel):
    sku_id: str
    quantity: int = Field(ge=1, le=999)


class ReserveRequest(BaseModel):
    order_no: str = Field(max_length=32)
    expires_at: str | None = None
    items: list[ReserveItem] = Field(min_length=1, max_length=50)


class ReleaseRequest(BaseModel):
    order_no: str = Field(max_length=32)
    reason: str | None = None
    items: list[ReserveItem] | None = None


class ConfirmRequest(BaseModel):
    order_no: str = Field(max_length=32)
    event_id: str | None = None
    paid_at: str | None = None
    items: list[ReserveItem] = Field(min_length=1, max_length=50)


class BatchQueryRequest(BaseModel):
    sku_ids: list[str] = Field(min_length=1, max_length=100)


class CategoryCreate(BaseModel):
    parent_id: str | None = None
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)
    sort_order: int = 0


class SkuCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=64)
    price_cents: int = Field(ge=0)
    original_price_cents: int | None = None
    spec_text: str = Field(min_length=1, max_length=255)
    image_url: str | None = None
    initial_stock: int = 0
    low_stock_threshold: int = 10


class ProductCreate(BaseModel):
    category_id: str
    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = None
    brand: str | None = None
    description: str | None = None
    main_image_url: str | None = None
    skus: list[SkuCreate] = Field(min_length=1, max_length=50)


class ProductPatch(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    brand: str | None = None
    description: str | None = None
    main_image_url: str | None = None
    version: int | None = None