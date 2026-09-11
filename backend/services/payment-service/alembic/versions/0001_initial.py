"""Initial schema for payment-service."""

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
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_payments_payment_no ON payments (payment_no)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_payments_order_channel_active ON payments (order_no, channel) WHERE status IN ('PENDING', 'PROCESSING')"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_payments_third_party ON payments (channel, third_party_payment_id) WHERE third_party_payment_id IS NOT NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_refunds_refund_no ON refunds (refund_no)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_refunds_idempotency_key ON refunds (idempotency_key)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_tx_transaction_no ON payment_transactions (transaction_no)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_tx_third_party ON payment_transactions (channel, third_party_transaction_id) WHERE third_party_transaction_id IS NOT NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_outbox_events_event_id ON outbox_events (event_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_order_no ON payments (order_no)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_tx_order_no ON payment_transactions (order_no)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_tx_channel_time ON payment_transactions (channel, transaction_at)"))


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)