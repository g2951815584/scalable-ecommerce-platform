"""cart-service application configuration."""

from functools import lru_cache

from common.config import CommonSettings
from pydantic import Field


class CartSettings(CommonSettings):
    service_name: str = "cart-service"
    app_port: int = Field(default=8003, validation_alias="APP_PORT")

    catalog_service_url: str = Field(default="http://catalog-service:8002", validation_alias="CATALOG_SERVICE_URL")
    max_items_per_cart: int = Field(default=100, validation_alias="CART_MAX_ITEMS_PER_CART")
    max_item_quantity: int = Field(default=99, validation_alias="CART_MAX_ITEM_QUANTITY")
    redis_ttl_seconds: int = Field(default=2592000, validation_alias="CART_REDIS_TTL_SECONDS")


@lru_cache
def get_settings() -> CartSettings:
    return CartSettings()