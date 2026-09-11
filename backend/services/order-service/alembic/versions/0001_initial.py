"""Initial schema for order-service."""

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
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_order_no ON orders (order_no)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_user_idem ON orders (user_id, idempotency_key) WHERE idempotency_key IS NOT NULL"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_user_status_created ON orders (user_id, status, created_at DESC)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_order_items_order_no_sku ON order_items (order_no, sku_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_order_status_logs_order_no ON order_status_logs (order_no, created_at)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_outbox_events_event_id ON outbox_events (event_id)"))


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)