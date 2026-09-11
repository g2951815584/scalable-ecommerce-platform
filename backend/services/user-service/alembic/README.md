# User database migrations

Create Alembic revisions for the PostgreSQL `ecommerce_user` schema here.
The initial detailed design defines users, credentials, profiles, roles,
permissions, addresses, verification codes, refresh tokens, OAuth bindings,
audit logs and `outbox_events`.  The scaffold intentionally ships no implicit
migration; deployments should run `alembic upgrade head` after revisions are
reviewed.
