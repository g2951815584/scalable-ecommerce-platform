"""Notification templates, versions, records and channel configs."""

from datetime import datetime

from common.db import Base, IdMixin, TimestampMixin
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class NotificationTemplate(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_templates"

    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="TRANSACTIONAL")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationTemplateVersion(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_template_versions"

    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    title_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_records"

    record_no: Mapped[str] = mapped_column(String(32), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trigger_source: Mapped[str] = mapped_column(String(16), nullable=False, default="EVENT")
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recipient_masked: Mapped[str] = mapped_column(String(128), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    retry_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationChannelConfig(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_channel_configs"

    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=100)
    fallback_channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    daily_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class NotificationPreference(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    marketing_email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    marketing_sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)