# 设计：安全模型升级路径

Status: Approved

## 背景

BuyWise 当前 closed beta 使用受控 API key、scope 和 readiness token，适合小范围 Android 演示、后台运营和发布烟测。该模型不适合公网用户体系：token 无用户会话语义，轮换和撤销依赖配置发布，admin 操作缺少独立审计主体，未来如果接入真实购物、地址或支付会放大风险。

当前版本仍不纳入真实购物车、支付、地址簿和真实结算。订单接口继续表示 BuyWise 内部购买记录或 shadow order，用于导购反馈闭环。

## 方案

阶段 0 保持现状：

- 保留 `AUTH_API_KEYS`、scope、readiness token 和 admin JWT secret。
- closed beta token 只发给受控测试主体，scope 按最小权限配置。
- release smoke 使用独立 smoke subject，便于过滤测试订单和评价。

阶段 1 引入用户主体抽象：

- 在 `AuthProvider` 内部把 API key principal、admin principal 和未来 OIDC/JWT principal 统一成同一 `Principal`。
- service 层只接收 `subject`、`scopes`、`auth_type` 和可选 `tenant_id`，不感知 token 格式。
- 订单、评价、上传和管理接口记录稳定 subject，避免把 bearer token 或第三方 claim 原文写入业务表。

阶段 2 引入 OIDC/JWT：

- 新增 OIDC issuer、audience、JWKS URL、clock skew、required claims 配置域。
- 公网用户路由接受短期 JWT；后台管理使用独立 admin issuer 或 admin role claim。
- API key 仅保留给服务间调用、release smoke 和紧急运维，不作为公网用户登录方式。

阶段 3 token rotation 和撤销：

- API key 支持 key id、创建时间、过期时间和双 key 灰度窗口。
- JWT 依赖 issuer 的短期 token 和 refresh token 策略；后端只校验 access token。
- 高风险 admin scope 支持 denylist 或版本号 claim，用于强制撤销。

阶段 4 admin audit log：

- 管理类写操作记录 audit event，至少包含 request id、subject、auth type、scope、route、目标资源、变更摘要、结果和错误原因。
- audit log 不记录 secret、token、密码、原始大 payload 或用户隐私字段。
- closed beta release 记录引用相关 admin 操作和 smoke subject。

## 影响

- `app.core.auth_provider`：扩展 principal 字段和 OIDC/JWT 校验入口。
- `app.core.config`：新增 OIDC/JWT 与 token rotation 配置域。
- `app.api.v1.admin`：接入 admin principal 和 audit event。
- `app.services.order_service`、`app.services.review_workflow_service`、`app.services.upload_service`：继续只依赖稳定 subject。
- `docs/reference/api.md`、`docs/reference/configuration.md`：同步 auth scheme 和 scope 变化。
- Android：公网用户登录前继续使用 closed beta token；引入 OIDC 后再新增登录态管理。

## 验证

- auth provider 单元测试覆盖 API key、JWT、scope、过期、audience 和 issuer 错误。
- API contract 测试覆盖公开路由、用户路由、admin 路由的 401/403 行为。
- admin audit log 测试覆盖成功、失败和敏感字段脱敏。
- release smoke 使用独立 smoke subject，并确认不会泄露 token。

## 最近检查

2026-05-31
