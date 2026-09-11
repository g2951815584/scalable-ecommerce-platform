"""Initial schema for user-service."""

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

    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_users_email ON users (email) WHERE deleted_at IS NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_users_phone ON users (phone) WHERE deleted_at IS NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_user_credentials_user_id ON user_credentials (user_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_user_profiles_user_id ON user_profiles (user_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_roles_code ON roles (code)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_permissions_code ON permissions (code)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_role_permissions_role_id_permission_id ON role_permissions (role_id, permission_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_user_roles_user_id_role_id ON user_roles (user_id, role_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_user_addresses_default ON user_addresses (user_id) WHERE is_default = TRUE AND deleted_at IS NULL"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_refresh_tokens_token_hash ON refresh_tokens (token_hash)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_oauth_bindings_provider_provider_user_id ON oauth_bindings (provider, provider_user_id)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_oauth_bindings_user_id_provider ON oauth_bindings (user_id, provider)"))
    bind.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uk_outbox_events_event_id ON outbox_events (event_id)"))

    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_users_status_created_at ON users (status, created_at DESC)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_user_addresses_user_id_created_at ON user_addresses (user_id, created_at DESC)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_verification_codes_account_scene ON verification_codes (account, scene, created_at DESC)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id_status ON refresh_tokens (user_id, status)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS idx_user_audit_logs_user_id_created_at ON user_audit_logs (user_id, created_at DESC)"))

    _seed()


def _seed() -> None:
    bind = op.get_bind()
    roles = [
        (1, "BUYER", "注册买家", "SYSTEM", 10),
        (2, "PRODUCT_OPS", "商品运营", "SYSTEM", 20),
        (3, "ORDER_OPS", "订单运营", "SYSTEM", 30),
        (4, "WAREHOUSE", "仓储发货", "SYSTEM", 40),
        (5, "CS", "客服", "SYSTEM", 50),
        (6, "FINANCE", "财务", "SYSTEM", 60),
        (7, "ADMIN", "系统管理员", "SYSTEM", 70),
    ]
    for role in roles:
        bind.execute(text(
            "INSERT INTO roles (id, code, name, role_type, is_enabled, sort_order, created_at, updated_at) "
            "VALUES (:id, :code, :name, :rtype, TRUE, :sort, now(), now()) ON CONFLICT (id) DO NOTHING"
        ), {"id": role[0], "code": role[1], "name": role[2], "rtype": role[3], "sort": role[4]})

    permissions = [
        (1, "catalog:category:manage", "分类维护", "catalog"),
        (2, "catalog:product:manage", "商品维护", "catalog"),
        (3, "inventory:stock:view", "库存查询", "inventory"),
        (4, "inventory:stock:manage", "库存调整", "inventory"),
        (5, "order:order:view_all", "查看全部订单", "order"),
        (6, "order:order:modify_price", "订单改价", "order"),
        (7, "order:order:cancel", "订单取消/关闭", "order"),
        (8, "order:shipment:manage", "发货操作", "order"),
        (9, "after_sale:refund:review", "退款审核", "after_sale"),
        (10, "after_sale:refund:create", "发起退款", "after_sale"),
        (11, "finance:transaction:view", "交易流水查看", "finance"),
        (12, "finance:reconciliation:manage", "对账管理", "finance"),
        (13, "system:user:view", "用户检索", "system"),
        (14, "system:user:manage", "用户角色分配与启停", "system"),
        (15, "system:role:manage", "角色权限配置", "system"),
        (16, "system:notification_template:manage", "通知模板维护", "system"),
    ]
    for p in permissions:
        bind.execute(text(
            "INSERT INTO permissions (id, code, name, module, created_at, updated_at) "
            "VALUES (:id, :code, :name, :module, now(), now()) ON CONFLICT (id) DO NOTHING"
        ), {"id": p[0], "code": p[1], "name": p[2], "module": p[3]})

    role_permissions = {
        2: [1, 2, 3, 4],
        3: [5, 6, 7, 9, 10],
        4: [5, 8],
        5: [5, 7, 9, 10],
        6: [5, 11, 12],
        7: list(range(1, 17)),
    }
    counter = 1
    for role_id, perms in role_permissions.items():
        for perm_id in perms:
            bind.execute(text(
                "INSERT INTO role_permissions (id, role_id, permission_id, created_at, updated_at) "
                "VALUES (:id, :role, :perm, now(), now()) ON CONFLICT (id) DO NOTHING"
            ), {"id": 10000 + counter, "role": role_id, "perm": perm_id})
            counter += 1


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)