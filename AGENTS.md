# Repository Guidelines

## Project Structure & Module Organization

This pnpm workspace contains the e-commerce platform.

- `apps/storefront/` contains the buyer-facing React/Vite application; `apps/admin/` contains the operations console.
- `packages/frontend-shared/` holds shared TypeScript contracts, API helpers, formatting, and permissions.
- `backend/services/` contains FastAPI microservices (`user-service`, `catalog-service`, `cart-service`, `order-service`, `payment-service`, and `notification-service`). Keep routes, schemas, models, repositories, and tests inside the owning service.
- `backend/libs/common/` provides reusable Python middleware, responses, auth, IDs, events, and health helpers.
- `docs/` is the source of truth for requirements and detailed design; update relevant Chinese design documents when behavior changes.

## Build, Test, and Development Commands

Use Node.js 20+ and pnpm 10+:

```bash
pnpm install                         # install workspace dependencies
pnpm dev:storefront                  # run storefront on :5173
pnpm dev:admin                       # run admin app on :5174
pnpm build                           # build all packages/apps with scripts
pnpm typecheck                       # run TypeScript checks across the workspace
pnpm lint                            # run configured lint/type checks
pnpm test                            # run workspace test scripts
cd backend && uv sync                # install Python workspace dependencies
cd backend/services/user-service && uv run uvicorn app.main:app --reload --port 8001
cd backend && uv run pytest          # run backend tests (configured under services/*/tests)
```

`compose:up` and `compose:down` manage the Docker stack; copy `.env.example` to `.env` first.

## Coding Style & Naming Conventions

Use two-space indentation in TypeScript/TSX and four spaces in Python. Follow the existing TypeScript style: double quotes, semicolons, PascalCase React components, camelCase functions/variables, and kebab-case service directories. Python uses `snake_case` modules/functions and `PascalCase` classes. Keep API wire types in shared packages. Ruff enforces a 100-character Python line limit; TypeScript checks use `tsc`.

## Testing Guidelines

Backend tests use pytest and are named `test_*.py` under each service's `tests/` directory (for example, `backend/services/user-service/tests/unit/test_health.py`). Run focused tests with `uv run pytest services/user-service/tests/unit/test_health.py`. Frontend `test` scripts are placeholders; add coverage when introducing a test runner.

## Commit & Pull Request Guidelines

Use short, imperative messages in the established `<type>: <description>` format, such as `docs: ...`, `feat: ...`, `fix: ...`, or `test: ...`. Keep commits focused. Pull requests should explain the change, link the issue or design document, list validation commands, and include screenshots for storefront/admin UI changes. Call out configuration, migration, or API-contract changes.

## Security & Configuration Tips

Never commit `.env` files, credentials, tokens, or production connection strings. Start from `.env.example`; replace placeholder secrets before deployment. Backend adapters are currently in-memory, so verify persistence and secret-manager integration before treating local behavior as production-ready.
