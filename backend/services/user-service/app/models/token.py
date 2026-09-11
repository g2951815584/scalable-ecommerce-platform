"""Verification codes (hashed at rest) and refresh tokens."""

from datetime import datetime
from uuid import UUID

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, DateTime, SmallInteger, String, Uuid
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column


class VerificationCode(IdMixin, TimestampMixin, Base):
    __tablename__ = "verification_codes"

    account: Mapped[str] = mapped_column(String(254), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scene: Mapped[str] = mapped_column(String(32), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=5)
    sender_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RefreshToken(IdMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_family_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    parent_token_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    revoke_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)