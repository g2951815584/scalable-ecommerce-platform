"""SQLAlchemy models for catalog-service."""

from common.outbox import OutboxEvent

from .inventory import Inventory, InventoryTransaction, StockReservation
from .misc import LowStockAlert, ProductChangeLog, ProductTagRel, Review, ReviewReply, Tag
from .product import Category, ProductAttribute, ProductImage, Sku, Spu

__all__ = [
    "Category",
    "Inventory",
    "InventoryTransaction",
    "LowStockAlert",
    "OutboxEvent",
    "ProductAttribute",
    "ProductChangeLog",
    "ProductImage",
    "ProductTagRel",
    "Review",
    "ReviewReply",
    "Sku",
    "Spu",
    "StockReservation",
    "Tag",
]