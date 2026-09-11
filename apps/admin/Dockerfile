FROM node:20-slim AS builder
WORKDIR /workspace
COPY package.json pnpm-workspace.yaml tsconfig.base.json ./
COPY packages/frontend-shared/package.json packages/frontend-shared/tsconfig.json ./packages/frontend-shared/
COPY packages/frontend-shared/src ./packages/frontend-shared/src
COPY apps/admin/package.json apps/admin/tsconfig.json apps/admin/tsconfig.app.json apps/admin/tsconfig.node.json apps/admin/vite.config.ts ./apps/admin/
COPY apps/admin/index.html ./apps/admin/index.html
COPY apps/admin/src ./apps/admin/src
RUN corepack enable && pnpm install --no-frozen-lockfile && pnpm --filter @ecommerce/admin build

FROM nginx:alpine
COPY apps/admin/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /workspace/apps/admin/dist /usr/share/nginx/html/admin
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -qO- http://localhost/admin/ || exit 1
