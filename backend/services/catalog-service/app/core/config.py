"""catalog-service application configuration."""

from functools import lru_cache

from common.config import CommonSettings
from pydantic import Field


class CatalogSettings(CommonSettings):
    service_name: str = "catalog-service"
    app_port: int = Field(default=8002, validation_alias="APP_PORT")

    # Inventory (three-phase reserve/confirm/release)
    order_reserve_ttl_seconds: int = Field(default=2100, validation_alias="ORDER_RESERVE_TTL_SECONDS")
    reserve_max_ttl_seconds: int = Field(default=7200, validation_alias="RESERVE_MAX_TTL_SECONDS")
    reserve_max_items: int = Field(default=50, validation_alias="RESERVE_MAX_ITEMS")
    batch_query_max_skus: int = Field(default=100, validation_alias="BATCH_QUERY_MAX_SKUS")
    low_stock_default_threshold: int = Field(default=10, validation_alias="LOW_STOCK_DEFAULT_THRESHOLD")

    # Internal clients
    order_service_url: str = Field(default="http://order-service:8004", validation_alias="ORDER_SERVICE_URL")


@lru_cache
def get_settings() -> CatalogSettings:
    return CatalogSettings()