"""notification-service application configuration."""

from functools import lru_cache

from common.config import CommonSettings
from pydantic import Field


class NotificationSettings(CommonSettings):
    service_name: str = "notification-service"
    app_port: int = Field(default=8006, validation_alias="APP_PORT")

    user_service_url: str = Field(default="http://user-service:8001", validation_alias="USER_SERVICE_URL")
    site_base_url: str = Field(default="https://shop.example.com", validation_alias="NOT_SITE_BASE_URL")
    ops_alert_emails: str = Field(default="ops@example.com", validation_alias="NOT_OPS_ALERT_EMAILS")
    vcode_cooldown_seconds: int = Field(default=60, validation_alias="NOT_VCODE_COOLDOWN_SECONDS")


@lru_cache
def get_settings() -> NotificationSettings:
    return NotificationSettings()