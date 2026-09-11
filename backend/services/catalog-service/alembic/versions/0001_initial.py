"""Initial schema for catalog-service."""

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

    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_categories_slug ON categories (slug) WHERE deleted_at IS NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_skus_sku_code ON skus (sku_code) WHERE deleted_at IS NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_inventories_sku_id ON inventories (sku_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_stock_reservations_order_sku ON stock_reservations (order_no, sku_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_outbox_events_event_id ON outbox_events (event_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_spus_status_category_id ON spus (status, category_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_skus_spu_id ON skus (spu_id, sort_order)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_reservations_status_expires_at ON stock_reservations (expires_at) WHERE status = 'RESERVED'"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_sku_created ON inventory_transactions (sku_id, created_at DESC)"))

    bind.execute(text(
        "INSERT INTO tags (id, code, name, tag_type, color, sort_order, is_enabled, created_at, updated_at) VALUES "
        "(1000000000000000001, 'NEW', '新品', 'AUTO', '#52C41A', 10, TRUE, now(), now()),"
        "(1000000000000000002, 'HOT', '热销', 'MANUAL', '#FA541C', 20, TRUE, now(), now()),"
        "(1000000000000000003, 'PROMO', '促销', 'MANUAL', '#EB2F96', 30, TRUE, now(), now()) "
        "ON CONFLICT (id) DO NOTHING"
    ))


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)