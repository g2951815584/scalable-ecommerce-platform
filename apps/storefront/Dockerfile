FROM node:20-slim AS builder
WORKDIR /workspace
COPY package.json pnpm-workspace.yaml tsconfig.base.json ./
COPY packages/frontend-shared/package.json packages/frontend-shared/tsconfig.json ./packages/frontend-shared/
COPY packages/frontend-shared/src ./packages/frontend-shared/src
COPY apps/storefront/package.json apps/storefront/tsconfig.json apps/storefront/tsconfig.app.json apps/storefront/tsconfig.node.json apps/storefront/vite.config.ts ./apps/storefront/
COPY apps/storefront/index.html ./apps/storefront/index.html
COPY apps/storefront/src ./apps/storefront/src
RUN corepack enable && pnpm install --no-frozen-lockfile && pnpm --filter @ecommerce/frontend-shared build && pnpm --filter @ecommerce/storefront build

FROM nginx:alpine
COPY apps/storefront/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /workspace/apps/storefront/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1/ || exit 1
