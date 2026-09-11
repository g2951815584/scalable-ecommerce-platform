"""payment-service application configuration."""

from functools import lru_cache

from common.config import CommonSettings
from pydantic import Field


class PaymentSettings(CommonSettings):
    service_name: str = "payment-service"
    app_port: int = Field(default=8005, validation_alias="APP_PORT")

    order_service_url: str = Field(default="http://order-service:8004", validation_alias="ORDER_SERVICE_URL")
    refund_audit_threshold_cents: int = Field(default=100000, validation_alias="PAYMENT_REFUND_AUDIT_THRESHOLD_CENTS")
    refund_max_retry: int = Field(default=3, validation_alias="PAYMENT_REFUND_MAX_RETRY")


@lru_cache
def get_settings() -> PaymentSettings:
    return PaymentSettings()