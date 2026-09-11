# Repository Guidelines

## 项目结构与模块组织

这是一个 pnpm + uv 管理的电商微服务 monorepo：

- `apps/storefront` 与 `apps/admin`：基于 React/Vite 的买家端和运营后台，源码位于各自的 `src/`。
- `packages/frontend-shared`：前端共享的 API client、契约、权限和格式化工具。
- `backend/services/*-service`：六个 FastAPI 服务（用户、目录、购物车、订单、支付、通知）；按 `api/`、`services/`、`models/`、`tests/` 分层。
- `backend/libs/common`：跨服务的认证、响应、事件、数据库和中间件基础库。
- `backend/scripts`：种子数据、冒烟测试与 E2E 脚本；`infra/` 保存 Docker Compose、Traefik 与数据库初始化；`docs/` 保存需求和设计文档，是需求与行为变更的事实来源。

## 构建、测试与本地开发

先安装 Node 20+、pnpm 10+、Python 3.12+、uv 和 Docker。常用命令：

```bash
pnpm install --frozen-lockfile     # 安装前端依赖
pnpm dev:storefront               # 启动买家端（5173）
pnpm dev:admin                    # 启动后台（5174）
pnpm typecheck                    # 全部 TypeScript 类型检查
pnpm build                        # 递归构建前端包
pnpm lint                         # 运行各包已配置的 lint（当前前端为 tsc）
pnpm test                         # 递归运行已配置测试
docker compose --env-file .env -f infra/docker-compose.yml up --build
docker compose --env-file .env -f infra/docker-compose.yml down  # 停止并移除本地栈
```

后端可在 `backend/` 执行 `uv sync --all-packages`、`uvx ruff check .`；单服务测试示例：`cd backend/services/order-service && PYTHONPATH=. uv run --project ../.. pytest -q`。完整 E2E 流程参考 `.github/workflows/ci.yml`，包括迁移、`backend/scripts/seed_data.py` 和 `e2e_checkout.py`。

## 编码风格与命名

Python 使用 4 空格、Ruff（行宽 100，目标 Python 3.12）；模块和函数用 `snake_case`，类用 `PascalCase`。TypeScript/React 使用 2 空格、ES modules；组件使用 `PascalCase`，变量和函数使用 `camelCase`。共享接口优先放入 `packages/frontend-shared` 或 `backend/libs/common`，避免跨服务直接导入实现细节。

## 测试指南

后端测试框架为 Pytest（配置于 `backend/pyproject.toml`），测试放在对应服务的 `tests/`，文件命名为 `test_*.py`；新增业务逻辑应覆盖成功、校验失败和关键补偿路径。前端目前没有真实测试套件，`apps/*/package.json` 的 `test` 仅为占位脚本，因此提交前至少运行类型检查和构建。

## 提交与 Pull Request

Git 历史采用 Conventional Commits 风格，如 `feat:`、`fix:`、`test:`、`docs:`、`ci:`，主题使用祈使、简洁描述。PR 应说明目的和影响范围，关联 issue（如有），列出验证命令；UI 变更附截图或录屏，API/数据迁移变更注明兼容性与回滚注意事项。提交前应确保 CI 的后端 lint/单测、前端 typecheck/build 和 Compose E2E 均通过。

## 安全与配置

不要提交真实凭据或根目录 `.env`；从 `.env.example` 复制并通过密钥管理器注入 `DATABASE_URL`、`REDIS_URL`、`RABBITMQ_URL`、`JWT_PUBLIC_KEY` 与 `INTERNAL_TOKEN`。当前默认适配器为内存实现，仅适合本地 smoke 测试。
