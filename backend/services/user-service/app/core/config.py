from functools import lru_cache

from common.config import CommonSettings
from pydantic import Field


class UserSettings(CommonSettings):
    service_name: str = "user-service"
    app_port: int = Field(default=8001, validation_alias="APP_PORT")

    # JWT (RS256). The private key lives only in this service; the gateway and
    # peer services hold the public key.
    jwt_private_key: str = Field(default="", validation_alias="JWT_PRIVATE_KEY")
    jwt_public_key: str = Field(default="", validation_alias="JWT_PUBLIC_KEY")
    jwt_issuer: str = Field(default="user-service", validation_alias="JWT_ISSUER")
    jwt_audience: str = Field(default="ecommerce-platform", validation_alias="JWT_AUDIENCE")
    access_token_ttl_seconds: int = Field(default=1800, validation_alias="JWT_ACCESS_TTL_SECONDS")
    refresh_token_ttl_seconds: int = Field(default=1209600, validation_alias="JWT_REFRESH_TTL_SECONDS")

    # Hashes and peppers
    refresh_token_pepper: str = Field(default="", validation_alias="REFRESH_TOKEN_PEPPER")
    verify_code_pepper: str = Field(default="", validation_alias="VERIFY_CODE_PEPPER")

    # Argon2id parameters (O(64MiB) memory, 3 iterations per the design).
    argon2_time_cost: int = Field(default=3, validation_alias="ARGON2_TIME_COST")
    argon2_memory_cost_kib: int = Field(default=65536, validation_alias="ARGON2_MEMORY_COST_KIB")
    argon2_parallelism: int = Field(default=4, validation_alias="ARGON2_PARALLELISM")
    password_min_length: int = Field(default=8, validation_alias="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=64, validation_alias="PASSWORD_MAX_LENGTH")

    # Verification codes
    verify_code_length: int = Field(default=6, validation_alias="VERIFY_CODE_LENGTH")
    verify_code_email_ttl_seconds: int = Field(default=600, validation_alias="VERIFY_CODE_EMAIL_TTL_SECONDS")
    verify_code_sms_ttl_seconds: int = Field(default=300, validation_alias="VERIFY_CODE_SMS_TTL_SECONDS")
    verify_code_max_attempts: int = Field(default=5, validation_alias="VERIFY_CODE_MAX_ATTEMPTS")
    verify_code_send_interval_seconds: int = Field(default=60, validation_alias="VERIFY_CODE_SEND_INTERVAL_SECONDS")
    verify_code_daily_limit_per_account: int = Field(default=10, validation_alias="VERIFY_CODE_DAILY_LIMIT_PER_ACCOUNT")
    verify_code_daily_limit_per_ip: int = Field(default=30, validation_alias="VERIFY_CODE_DAILY_LIMIT_PER_IP")

    # Login safety
    login_max_failures: int = Field(default=5, validation_alias="LOGIN_MAX_FAILURES")
    login_lock_minutes: int = Field(default=15, validation_alias="LOGIN_LOCK_MINUTES")

    # Addresses
    address_max_count: int = Field(default=20, validation_alias="ADDRESS_MAX_COUNT")

    # Account close
    account_close_cooling_days: int = Field(default=30, validation_alias="ACCOUNT_CLOSE_COOLING_DAYS")
    account_close_require_order_check: bool = Field(default=True, validation_alias="ACCOUNT_CLOSE_REQUIRE_ORDER_CHECK")

    # Internal clients
    notification_service_url: str = Field(default="http://notification-service:8006", validation_alias="NOTIFICATION_SERVICE_URL")
    order_service_url: str = Field(default="http://order-service:8004", validation_alias="ORDER_SERVICE_URL")

    @property
    def has_jwt_keys(self) -> bool:
        return bool(self.jwt_private_key) and bool(self.jwt_public_key)


@lru_cache
def get_settings() -> UserSettings:
    return UserSettings()
