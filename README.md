# Scalable E-Commerce Platform

一个面向可扩展性的电商微服务平台示例，包含买家商城、运营管理后台、六个 FastAPI 后端服务，以及 PostgreSQL、Redis、RabbitMQ、Consul 和 Traefik 基础设施。当前代码重点展示服务边界、API 契约、事件驱动流程和本地 Compose 运行方式。

## 项目结构

```text
apps/                  React/Vite 买家端与运营后台
packages/frontend-shared 前端共享契约、请求客户端与工具
backend/services/      user、catalog、cart、order、payment、notification
backend/libs/common    跨服务 Python 基础库
backend/scripts/        种子数据、冒烟测试和端到端脚本
infra/                 Docker Compose、Traefik、网关与数据库初始化
docs/                   需求规格、概要架构和详细设计
```

## 快速开始

环境要求：Node.js 20+、pnpm 10+、Python 3.12+、uv 和 Docker。

```bash
cp .env.example .env
pnpm install --frozen-lockfile
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

启动后，网关入口为 `http://localhost:8080`，买家端和后台分别使用 5173、5174（直接运行 Vite 时）。基础设施端口包括 PostgreSQL 5432、Redis 6379、RabbitMQ 管理界面 15672、Consul 8500 和 Traefik Dashboard 8081。停止本地栈：

```bash
docker compose --env-file .env -f infra/docker-compose.yml down
```

## 开发与验证

```bash
pnpm dev:storefront       # 买家端
pnpm dev:admin            # 运营后台
pnpm typecheck            # 前端类型检查
pnpm build                # 递归构建前端包
cd backend && uv sync --all-packages
cd backend && uvx ruff check .
cd backend && uv run pytest
```

完整 E2E 流程会启动 Compose 栈、执行 Alembic 迁移、写入演示数据并运行 `backend/scripts/e2e_checkout.py`；CI 中的完整步骤见 [.github/workflows/ci.yml](.github/workflows/ci.yml)。单个服务可在其目录运行，例如 `cd backend/services/order-service && PYTHONPATH=. uv run --project ../.. pytest -q`。

## 文档与贡献

开发前请阅读 [`docs/03-详细设计/00-通用约定.md`](docs/03-详细设计/00-通用约定.md)，它定义了响应格式、认证、幂等、事件和日志约定。贡献流程、命名规则、提交格式和安全要求见 [`AGENTS.md`](AGENTS.md)。提交信息采用 Conventional Commits，例如 `feat: add order export`、`fix: handle payment callback retry`；PR 请说明变更范围、验证命令，并为 UI 变更附截图或录屏。

## 配置与安全

`.env.example` 仅包含本地占位值；不要提交真实密钥、令牌或生产连接串。部署到非本地环境前，请通过密钥管理器注入 `JWT_PUBLIC_KEY`、`INTERNAL_TOKEN` 及数据库、缓存、消息队列凭据。当前默认适配器为内存实现，适用于本地 smoke 测试，不应直接视为生产持久化方案。
