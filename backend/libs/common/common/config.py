"""Environment-first service settings.

The settings object only describes the cross-service contract.  Service
modules extend it with their own knobs, keeping configuration at the seam and
avoiding hard-coded credentials in implementations.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    app_env: str = Field(default="dev", validation_alias="APP_ENV")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    service_name: str = Field(default="ecommerce-service", validation_alias="SERVICE_NAME")
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres", validation_alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", validation_alias="RABBITMQ_URL")
    jwt_public_key: str = Field(default="", validation_alias="JWT_PUBLIC_KEY")
    internal_token: str = Field(default="", validation_alias="INTERNAL_TOKEN")
    consul_host: str = Field(default="http://localhost:8500", validation_alias="CONSUL_HOST")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)


@lru_cache
def get_common_settings() -> CommonSettings:
    """Return one process-local settings snapshot."""

    return CommonSettings()
