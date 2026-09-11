"""Initial schema for notification-service."""

import app.models  # noqa: F401
from alembic import op
from common.db import Base
from sqlalchemy import text

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_templates_code ON notification_templates (template_code)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_template_versions_template_version ON notification_template_versions (template_id, version)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_records_record_no ON notification_records (record_no)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_records_event_template ON notification_records (event_id, template_code) WHERE event_id IS NOT NULL"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_records_created ON notification_records (created_at DESC, id DESC)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_records_user ON notification_records (user_id, created_at DESC)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_channel_configs ON notification_channel_configs (channel, provider)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_preferences_user ON notification_preferences (user_id)"))

    bind.execute(text(
        "INSERT INTO notification_channel_configs (id, channel, provider, is_enabled, priority, fallback_channel, daily_quota, config, created_at, updated_at) VALUES "
        "(1800000000000000001, 'EMAIL', 'SENDGRID', TRUE, 10, NULL, NULL, '{\"from_email\":\"noreply@shop.example.com\"}', now(), now()),"
        "(1800000000000000002, 'SMS', 'TWILIO', TRUE, 20, 'EMAIL', 5000, '{}', now(), now()) "
        "ON CONFLICT (id) DO NOTHING"
    ))


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)