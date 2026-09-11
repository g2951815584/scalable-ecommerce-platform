"""order-service application configuration."""

from functools import lru_cache

from common.config import CommonSettings
from pydantic import Field


class OrderSettings(CommonSettings):
    service_name: str = "order-service"
    app_port: int = Field(default=8004, validation_alias="APP_PORT")

    payment_timeout_minutes: int = Field(default=30, validation_alias="ORDER_PAYMENT_TIMEOUT_MINUTES")
    shipping_base_fee_cents: int = Field(default=800, validation_alias="ORDER_SHIPPING_BASE_FEE_CENTS")
    free_shipping_threshold_cents: int = Field(default=9900, validation_alias="ORDER_FREE_SHIPPING_THRESHOLD_CENTS")
    auto_confirm_days: int = Field(default=15, validation_alias="ORDER_AUTO_CONFIRM_DAYS")
    after_sale_days: int = Field(default=7, validation_alias="ORDER_AFTER_SALE_DAYS")
    max_item_kinds: int = Field(default=50, validation_alias="ORDER_MAX_ITEM_KINDS")

    cart_service_url: str = Field(default="http://cart-service:8003", validation_alias="CART_SERVICE_URL")
    catalog_service_url: str = Field(default="http://catalog-service:8002", validation_alias="CATALOG_SERVICE_URL")
    user_service_url: str = Field(default="http://user-service:8001", validation_alias="USER_SERVICE_URL")


@lru_cache
def get_settings() -> OrderSettings:
    return OrderSettings()