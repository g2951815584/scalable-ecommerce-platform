# 已知债务（Known Debt）

> 本文档是项目当前所有已知技术/功能债务的**唯一事实来源（Source of Truth）**。
> 使用 issue 追踪工具管理时，请以每条债务的 `DEBT-xxx` 编号作为 issue 与本文档之间的对应键。

## 元信息

| 项 | 内容 |
|---|---|
| 最后更新 | 2026-09-11 |
| 维护约定 | 新增/关闭债务时**同时**更新本文档与下游 issue；编号 `DEBT-xxx` 一经分配不复用 |
| 上游文档 | [需求规格说明书](./01-需求规格说明书.md)、[概要架构设计](./02-概要架构设计.md)、[通用设计约定](./03-详细设计/00-通用约定.md) |

## 与 issue 追踪工具的对应约定

1. **一文一债**：每条债务对应一个 issue，标题固定为 `DEBT-xxx：<标题>`。
2. **优先级即标签**：`P0` / `P1` / `P2` / `P3` 作为 issue 标签；可另建里程碑按批次排期。
3. **关闭条件以"验收标准"为准**：issue 只有在达到本文档该债务的"验收标准"后才允许关闭。
4. **闭环回写**：债务完成 → 关闭 issue → 将本文档该条状态改为 `DONE` 并移动到「已关闭」一节。

## 优先级定义

| 级别 | 定义 | 出问题的代价 |
|---|---|---|
| P0 | 资损 / 超卖 / 重复入账 / 越权 | 钱错、货错、账乱 |
| P1 | 核心闭环断裂 / 数据一致性 | 状态对不上、数据泄漏、跨服务状态错位 |
| P2 | 功能完整性 / 运维性 | 功能缺失、数据堆积、排查困难 |
| P3 | 体验 / 后续增强 | "更好用"，非必需 |

---

## 债务总览

| ID | 标题 | 优先级 | 所属服务 | 状态 | issue |
|---|---|---|---|---|---|
| DEBT-001 | 订单超时关闭任务未实装 | P1 | order-service | OPEN | - |
| DEBT-002 | 下单幂等兜底缺失（重复预占→库存泄漏） | P1 | order-service | OPEN | - |
| DEBT-003 | 支付发起金额未强校验（可篡改金额） | P1 | payment-service | OPEN | - |
| DEBT-004 | 购物车未异步落库持久化 | P1 | cart-service | OPEN | - |
| DEBT-005 | 事件消费重试/死信拓扑简化 | P1 | 各服务 events | OPEN | - |
| DEBT-006 | 支付对账接口与任务 | P2 | payment-service | OPEN | - |
| DEBT-007 | 后台订单检索 + 退款审核工作台 | P2 | order-service | OPEN | - |
| DEBT-008 | 交易流水查询与导出 | P2 | payment-service | OPEN | - |
| DEBT-009 | 商品评价（review）接口 | P2 | catalog-service | OPEN | - |
| DEBT-010 | 商品标签管理接口 | P2 | catalog-service | OPEN | - |
| DEBT-011 | 定时清理任务（令牌/验证码/outbox/审计） | P2 | 各服务 tasks | OPEN | - |
| DEBT-012 | 账号注销冷静期匿名化（account_purge） | P2 | user-service | OPEN | - |
| DEBT-013 | 订单 CSV 流式导出 | P2 | order-service | OPEN | - |
| DEBT-014 | 商品搜索 PG 全文检索 + trigram | P3 | catalog-service | OPEN | - |
| DEBT-015 | OAuth（Google/GitHub）登录 | P3 | user-service | OPEN | - |
| DEBT-016 | 大表归档（库存流水/订单冷热分表） | P3 | catalog/order | OPEN | - |

---

## P1 — 核心闭环与数据一致性

### DEBT-001 订单超时关闭任务未实装
- **作用**：`PENDING_PAYMENT` 订单超过 30 分钟未支付，由定时任务扫出 → 置 `CLOSING→CLOSED` → 发 `order.cancelled` 释放预占。
- **影响**：订单永远停在"待支付"，但 catalog 兜底任务已在 35 分钟释放预占——订单还挂着、库存却已放出，买家此时支付会触发 `CAT-5013`（支付成功但预占已释放），状态机卡死。
- **修复方向**：order-service 新增 `tasks/scheduler.py`，实现超时扫描（借助 `idx_orders_timeout_scan` 部分索引）+ 关闭流程复用 `transition`。
- **验收标准**：超时订单在规定时间内自动关闭且预占释放；与支付成功的 `CLOSING` 竞态仲裁正确（见 04-订单服务 6.5）。

### DEBT-002 下单幂等兜底缺失（重复预占→库存泄漏）
- **作用**：文档要求 Redis `SETNX` + 数据库唯一索引兜底（`uk_orders_user_idem`）。
- **影响**：同一 `Idempotency-Key` 重试会各自生成不同 `order_no`、各自 reserve 成功，第二个落库触发唯一键冲突返回 500，**但第二个 order_no 的预占无人释放**，造成账面库存泄漏。
- **修复方向**：落库前 Redis 抢占幂等键；捕获 `IntegrityError` 转查询返回首次订单；冲突时补偿释放本次预占。
- **验收标准**：同 `Idempotency-Key` 并发 N 次仅有 1 个订单、不产生多余预占，其余返回首次结果。

### DEBT-003 支付发起金额未强校验（可篡改金额）
- **作用**：按文档，金额一律以订单服务返回值为准。
- **影响**：`create_payment` 信任入参 `amount_cents`，且 order 侧 `handle_payment_succeeded` 不比对 `amount_cents == payable_amount_cents`，恶意客户端可改小金额支付。
- **修复方向**：payment 调 order `/internal/v1/orders/{no}/amount` 取权威金额；order 消费 `payment.succeeded` 时校验金额一致，不一致置异常单（`ORD-8003`）。
- **验收标准**：客户端传入错误金额被拒或按订单金额收款，不产生差额入账。

### DEBT-004 购物车未异步落库持久化
- **作用**：文档要求 Redis 主存储 + Stream 异步落 PostgreSQL（30 天 TTL + 惰性回源）。
- **影响**：Redis 故障或 TTL 过期即购物车全丢，跨设备持久化（FR-CART-009）不成立。
- **修复方向**：实现 `cart:sync:stream` 落库队列 + `cart_items`/`carts` 持久化 + 惰性回源重建。
- **验收标准**：Redis 清空后购物车可从 DB 回源恢复，写入不因 Redis 重启而丢。

### DEBT-005 事件消费重试/死信拓扑简化
- **作用**：消费失败应按 `1s/5s/30s/2m/10m` 退避、5 次后进死信落库告警。
- **影响**：MQ 抖动/故障时 `order.paid`（扣库存）、`order.cancelled`（释放库存）可能丢处理，存在库存与订单状态不一致窗口。
- **修复方向**：统一消费者封装，接入退避队列/`x-death` 重试计数 + 死信落库(`*_dead_letters`) + 告警。
- **验收标准**：消费失败可退避重试并最终进死信；重放死信幂等有效。

---

## P2 — 功能完整性与运维

### DEBT-006 支付对账接口与任务
- **作用**：按日拉取第三方账单与本地流水比对，输出差异清单并告警（FR-PAY-008）。
- **影响**：缺失则"支付侧漏账/错账"只能靠人工或日志发现，是资损兜底的最后防线。
- **修复方向**：payment-service 实现对账批次/差异表 + 每日对账任务 + admin 查询/导出接口。
- **验收标准**：对账任务可产出批次与差异明细，差异数 > 0 触发告警。

### DEBT-007 后台订单检索 + 退款审核工作台
- **作用**：order-service 缺 `GET /admin/orders`（多条件检索）、退款申请列表与审核接口。
- **影响**：admin 的订单列表、退款审核页面为占位，运营/客服无法工作。
- **修复方向**：order-service 补 admin 订单列表（含防全表扫描护栏）、退款申请/审核流程（联动 payment 创建退款单）。
- **验收标准**：后台可按条件检索订单、可受理/驳回退款并正确流转状态。

### DEBT-008 交易流水查询与导出
- **作用**：payment-service 缺流水列表（游标分页）与 CSV 导出（FR-PAY-007）。
- **影响**：财务无法查询/导出资金流水，对账也无本地汇总视图。
- **修复方向**：实现 `GET /admin/payments/transactions`（游标）+ 流式 CSV 导出。
- **验收标准**：可按渠道/类型/时间过滤查询流水并导出 CSV。

### DEBT-009 商品评价（review）接口
- **作用**：catalog-service 缺 reviews 路由（列表/发表/回复/评分聚合），FR-CAT-013 未落地。
- **影响**：买家确认收货后无法评价，storefront 评价页、admin 评价管理均空转。
- **修复方向**：实现评价增查 + 与 order-service `can-review` 校验 + 评分统计异步重算。
- **验收标准**：买家可对已完成订单 SKU 评价一次，评价列表与评分聚合正确展示。

### DEBT-010 商品标签管理接口
- **作用**：catalog-service 只建了标签字典，缺 admin 侧标签增删改/打标接口。
- **影响**：运营无法维护新品/热销/促销等标签。
- **修复方向**：实现 tags CRUD + `product_tag_rel` 打标（含 `expires_at` 自动摘除）。
- **验收标准**：可创建/编辑标签、为商品打标并在列表展示。

### DEBT-011 定时清理任务（令牌/验证码/outbox/审计）
- **作用**：`refresh_tokens`、`verification_codes`、`outbox_events`、审计日志需要周期性清理/归档。
- **影响**：不加清理会无限堆积膨胀，拖慢查询并占用存储。
- **修复方向**：各服务 scheduler 补 `*_cleanup`（条件删除，幂等）与审计日志归档任务。
- **验收标准**：过期令牌/验证码/已投递 outbox 被按保留期批量清理。

### DEBT-012 账号注销冷静期匿名化（account_purge）
- **作用**：注销 30 天后昵称/头像/简介等彻底匿名化，删除凭证与 OAuth 绑定（NFR-CP-004 合规）。
- **影响**：当前只置 `DELETED` + 改写邮箱/电话，30 天后无后续匿名化，合规不完整。
- **修复方向**：user-service 实现 `account_purge` 任务（30 天冷静期后匿名化，幂等）。
- **验收标准**：注销用户 30 天后资料被匿名化、凭证删除，审计保留。

### DEBT-013 订单 CSV 流式导出
- **作用**：`GET /admin/orders/export` 流式导出 CSV（FR-ORD-013）。
- **影响**：运营/财务无法导出订单明细。
- **修复方向**：order-service 实现 keyset 游标 + StreamingResponse 导出，按角色脱敏。
- **验收标准**：可流式导出订单 CSV（不 OOM、行数上限、审计留痕）。

---

## P3 — 体验与后续增强

### DEBT-014 商品搜索 PG 全文检索 + trigram
- **作用**：用 PG `tsvector` + `pg_trgm` 替代当前 `ILIKE`，支持分词/相关度/错字兜底。
- **影响**：中文关键词仅精确子串匹配，无相关度与模糊兜底。
- **修复方向**：搜索集中在 `services/search.py`，实现 FTS + trigram 兜底（预留 ES 切换点）。
- **验收标准**：中文关键词可命中、错写可由 trigram 兜底，P95 延迟达标。

### DEBT-015 OAuth（Google/GitHub）登录
- **作用**：第三方授权码登录/绑定/解绑（FR-US-010）。
- **影响**：功能缺失，优先级低；可通过不注入 client id 直接关闭。
- **修复方向**：实现 author 授权地址 + callback（state+PKCE）+ 自动注册/绑定。
- **验收标准**：Google/GitHub 可登录并正确绑定本地账号（stub 第三方）。

### DEBT-016 大表归档（库存流水/订单冷热分表）
- **作用**：`inventory_transactions`、`product_change_logs`、`orders` 到千万级后归档/分区。
- **影响**：当前量级单表够用；长期增长后查询与写入退化。
- **修复方向**：按文档预留的归档冷表 + 搬迁任务（先拷后删、可重入）。
- **验收标准**：终态订单/历史流水可归档，详情查询对调用方透明。

---

## 已关闭（DONE）

| 编号 | 标题 | 完成阶段 | 说明 |
|---|---|---|---|
| DEBT-017 | 前端占位页 | 阶段 7 | storefront/admin 已接真实后端接口 |
| DEBT-018 | Traefik 网关 + 认证 | 阶段 7 | 网关路由/白名单/身份注入/剥离伪造头 |
| DEBT-019 | 下单 Saga 库存预占串联 | 阶段 8 | 下单 reserve / 取消 release 补偿闭环 |