"""Initial schema for cart-service."""

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
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_carts_owner_key ON carts (owner_key)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_cart_items_cart_sku ON cart_items (cart_id, sku_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_cart_items_cart_id ON cart_items (cart_id, created_at DESC)"))


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)