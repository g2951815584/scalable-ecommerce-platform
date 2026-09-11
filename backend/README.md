# Backend services scaffold

This directory contains the six Python/FastAPI service modules described in
`docs/03-详细设计`.  Each service is intentionally small at this stage: it
exposes the documented HTTP seams, uses an in-memory adapter for local smoke
tests, and leaves PostgreSQL/Redis/RabbitMQ integrations behind the repository
and client seams.  Replacing an adapter does not require changing the route
contracts.

## Services

| Service | Port | Database | Prefix |
| --- | ---: | --- | --- |
| `user-service` | 8001 | `ecommerce_user` | `/api/v1/auth`, `/api/v1/users` |
| `catalog-service` | 8002 | `ecommerce_catalog` | `/api/v1/products`, `/api/v1/categories` |
| `cart-service` | 8003 | `ecommerce_cart` | `/api/v1/cart` |
| `order-service` | 8004 | `ecommerce_order` | `/api/v1/orders` |
| `payment-service` | 8005 | `ecommerce_payment` | `/api/v1/payments` |
| `notification-service` | 8006 | `ecommerce_notification` | `/api/v1/notifications` |

## Local run

Install a service with `uv` (or pip), then run its module:

```bash
cd backend/services/user-service
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

The service Dockerfiles are built from the `backend/` context so the shared
`libs/common` package is available.  They use a non-root runtime user and
provide `/health` and `/ready` probes as required by the platform design.

The current adapters are deliberately in-memory and are **not** production
storage.  Set `DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `JWT_PUBLIC_KEY` and
`INTERNAL_TOKEN` from a secret manager before connecting real adapters.

## Shared contracts

`libs/common` provides the common response envelope, trace/request middleware,
header-based identity dependencies, readiness helpers, and the versioned event
envelope (`user.registered`, `order.created`, `order.paid`, etc.).  Domain
modules should depend on these interfaces rather than importing another
service's repositories.
