# 设计：普通用户账号登录系统

Status: Implemented

## 背景

BuyWise 当前有三类身份能力：后台管理员 JWT、`AUTH_API_KEYS` scope token、Android closed beta 构建 token。它们适合后台运营、受控 beta 和演示联调，但不适合作为公网普通用户账号系统。

普通用户账号系统的目标是让 Android 用户用手机号验证码登录，获得稳定用户身份，并让订单、评价、上传等用户能力逐步从 beta token 迁移到真实用户主体。评审演示仍需要低摩擦入口，因此游客模式定义为 Android 本机演示入口，不引入后端匿名账号体系。

## 方案

第一版普通用户登录使用中国大陆手机号和验证码。输入允许 `13812345678` 或 `+8613812345678`，后端统一规范化为 E.164 格式，例如 `+8613812345678`。验证码验证成功后自动注册或登录用户，不做独立注册页。第一版只支持中国大陆手机号，国际区号二期扩展。

短信服务第一版不接真实厂商。后端实现 OTP provider 抽象，dev/test 使用 mock 验证码，演示固定验证码为 `123456`。`APP_ENV=dev/test` 下 OTP request 可以返回 `debug_otp`，prod 永远不返回验证码；prod 如未配置真实短信 provider，不允许手机号 OTP 请求伪装成功。

核心接口：

- `POST /api/v1/auth/otp/request`：请求登录验证码。
- `POST /api/v1/auth/otp/verify`：校验验证码，自动创建或登录用户，并签发 token。
- `POST /api/v1/auth/refresh`：使用 refresh token 换取新的 access token 和 refresh token。
- `POST /api/v1/auth/logout`：撤销当前 refresh token。
- `GET /api/v1/auth/me`：返回当前登录用户的只读资料。

登录成功后返回短期 access JWT 和长期 refresh token。access token 建议 15 分钟有效，refresh token 默认 30 天有效。refresh token 使用高熵随机字符串，服务端只存哈希，客户端只在签发时拿到明文一次。refresh 成功时轮换 refresh token；已撤销或已轮换 token 再次出现时视为 replay，撤销当前 session。

用户 JWT 与后台管理员 JWT 完全分离。新增独立配置：

- `USER_JWT_SECRET`
- `USER_JWT_EXPIRE_MINUTES`
- `USER_REFRESH_TOKEN_EXPIRE_DAYS`

用户 access JWT claims 不包含手机号等 PII，至少包含：

- `sub`: `user:<id>`
- `typ`: `access`
- `auth_type`: `user`
- `jti`
- `iat`
- `exp`

`AuthProvider` 扩展为同时识别现有 `AUTH_API_KEYS` 和普通用户 JWT。普通用户 principal 使用固定最小 scope：`orders:read`、`orders:write`、`feedback:read`、`feedback:write`、`upload:write`。不授予 `products:write` 或后台权限。admin 路由继续只接受 admin JWT。

第一版用户资料保持最小：

- `id`
- `phone_e164`
- `display_name`
- `avatar_url`
- `status`: `active` 或 `disabled`
- `phone_verified_at`
- `last_login_at`
- `created_at`
- `updated_at`

手机号明文规范化存储并加唯一索引，API 响应只返回脱敏手机号，例如 `+86138****5678`。日志不得记录完整手机号、验证码、refresh token、access token 或 Authorization header。

OTP challenge 只存验证码哈希，不存明文。建议字段包括 `phone_e164`、`code_hash`、`purpose`、`expires_at`、`attempt_count`、`consumed_at`、`request_ip_hash` 和 `created_at`。验证码有效期 5 分钟，同一 challenge 最多验证 5 次。

基础防刷规则：

- 同一手机号 60 秒内只能请求 1 次。
- 同一手机号每小时最多 5 次，每天最多 20 次。
- 同一 IP 每分钟最多 10 次，每小时最多 100 次。
- 响应文案不泄露手机号是否已注册。
- dev/test 可使用固定验证码，但仍保留冷却、过期和尝试次数路径。

多设备登录通过 session 表支持。每个 refresh token 对应一个用户 session，可单独 logout，未来可支持退出其他设备。建议字段包括 `user_id`、`refresh_token_hash`、`device_id`、`device_name`、`created_at`、`last_used_at`、`expires_at`、`revoked_at`、`rotated_at`。

账号禁用第一版只做软禁用，不做完整注销。登录和 refresh 时必须检查 `users.status`；disabled 用户不能登录，refresh 时撤销 session 并返回 `account_disabled`。普通业务接口第一版不每次查用户表，依赖短期 access token 将禁用生效延迟控制在 15 分钟内。

现有身份兼容：

- 用户 JWT 是普通用户能力的主身份。
- `AUTH_API_KEYS` 保留给 closed beta、release smoke、服务间调用和评审体验 token。
- 订单、评价、上传第一版继续使用 `principal.subject`，避免把登录系统扩大成历史数据外键迁移。
- `DEMO_USER_REF` 只保留 dev/test 演示，不进入 prod 用户流。

Android 体验：

- 新增“我的/账号”入口。
- 未登录时展示手机号验证码登录入口和“游客体验”入口。
- 游客体验只是本机演示状态，不向后端创建 guest user，不签发 guest token。
- 游客可浏览商品、对比、AI 导购等匿名能力。
- 评审演示需要订单、评价、上传等受保护能力时，演示环境继续使用 `BUYWISE_BETA_TOKEN` 作为体验 token。
- 已登录用户显示脱敏手机号、基础资料和退出登录。
- App 启动时如存在 refresh token，自动 refresh 恢复登录态。
- 受保护 API 返回 401 时，Android refresh 成功后最多重试原请求一次。

第一版不做资料编辑、不做头像上传、不做收货地址、实名、支付信息、会员等级、游客后端身份、游客数据迁移、真实短信供应商、幂等键。幂等键二期补充，重点覆盖创建订单、提交评价、上传等写接口。

## 影响

后端新增或调整：

- API 层新增普通用户认证路由，并在 v1 router 中注册。
- Model 层新增普通用户、OTP challenge、用户 session 模型。
- Repository 层新增用户、OTP、session repository。
- Service 层新增普通用户 auth service、OTP service、token service。
- Auth provider 识别用户 access JWT，并保持 API key 兼容。
- Config 增加用户 JWT、refresh token、OTP 配置。
- Schema 层新增 auth 请求与响应 schema。
- Alembic 新增用户认证相关表迁移。
- Tests 新增认证核心测试和 scope 兼容测试。

Android 新增或调整：

- Data 层新增 auth DTO、token store、401 refresh retry。
- ViewModel 层新增登录态管理。
- UI screens 新增账号页、手机号验证码登录页、游客体验入口。
- 现有 repository 从固定 beta token 迁移到“用户 token 优先，演示 token 兼容”。

文档新增或更新：

- `docs/reference/api.md`：补充普通用户 auth API。
- `docs/reference/configuration.md`：补充用户 JWT、OTP、演示 token 配置。
- `docs/architecture/backend-boundaries.md`：补充用户认证边界。
- `docs/architecture/android-boundaries.md`：补充 Android 登录态边界。

## 验证

后端测试至少覆盖：

- OTP request 的手机号格式、冷却、频率限制、dev/test `debug_otp`。
- OTP verify 的正确验证码、错误验证码、过期、尝试次数、自动创建用户、disabled 用户拒绝。
- token 签发的 access JWT claims、不含手机号、refresh token 只存哈希。
- refresh 成功轮换、旧 token replay 撤销 session、disabled 用户 refresh 失败。
- logout 撤销当前 session。
- `/auth/me` 返回脱敏手机号和只读资料。
- 用户 JWT 可访问订单、评价、上传 scope，不能访问 admin 路由或 `products:write`。
- API key 兼容路径不回退。

Android 验证至少覆盖：

- 游客体验入口不要求登录。
- 手机号验证码登录成功后 token 持久化。
- App 启动时 refresh 恢复登录态。
- 401 后 refresh 并最多重试一次。
- 退出登录清空 token。
- 未登录访问用户能力时跳转登录，匿名浏览能力不受影响。

提交前运行相关后端测试。修改 docs 时运行 `python scripts/validate_docs.py`。

## 实现进度/剩余边界

- 已实现手机号 OTP request/verify、dev/test debug OTP、access JWT、refresh token 哈希存储与轮换、logout、`/auth/me`、用户 JWT scope 兼容、prod 配置校验和 Android auth DTO/token store/repository 接入。
- 真实短信供应商、资料编辑、头像上传、收货地址、实名、支付信息、会员等级、游客后端身份、游客数据迁移和写接口幂等键仍不在第一版范围内。

## 最近检查

2026-06-07
