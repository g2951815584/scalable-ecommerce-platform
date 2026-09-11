"""User aggregate: account, credentials and profile."""

from datetime import date, datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, Date, DateTime, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    registered_from: Mapped[str] = mapped_column(String(32), nullable=False, default="WEB")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def can_place_order(self) -> bool:
        return self.status == "ACTIVE" and (self.is_email_verified or self.is_phone_verified)


class UserCredential(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_credentials"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_algo: Mapped[str] = mapped_column(String(32), nullable=False, default="argon2id")
    password_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    failed_attempt_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    password_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gender: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-CN")
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
