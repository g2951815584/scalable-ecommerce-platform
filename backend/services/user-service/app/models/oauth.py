"""OAuth bindings and append-only audit logs."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column


class OAuthBinding(IdMixin, TimestampMixin, Base):
    __tablename__ = "oauth_bindings"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    is_email_verified_by_provider: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bound_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserAuditLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_audit_logs"

    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_type: Mapped[str] = mapped_column(String(32), nullable=False, default="USER")
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    client_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)