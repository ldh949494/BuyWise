# 配置参考

环境变量示例文件位于 `.env.dev.example`、`.env.test.example` 和 `.env.prod.example`。

## 应用

- `APP_NAME`
- `APP_ENV`
- `APP_PORT`
- `APP_DEBUG`
- `API_V1_PREFIX`
- `LOG_LEVEL`

## 数据库

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `SQLALCHEMY_ECHO`

Alembic 通过 `app.core.config.Settings.database_url` 使用同一组数据库配置。

## AI 与存储

- `CHROMA_PERSIST_DIR`
- `CHROMA_PRODUCT_COLLECTION`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `LLM_PROVIDER`
- `VISION_PROVIDER`
- `VISION_BASE_URL`
- `VISION_API_KEY`
- `VISION_MODEL`
- `SPEECH_PROVIDER`
- `TENCENT_SECRET_ID`
- `TENCENT_SECRET_KEY`
- `TENCENT_ASR_REGION`
- `TENCENT_ASR_ENGINE_MODEL_TYPE`
- `TENCENT_ASR_VOICE_FORMAT`
- `COS_BUCKET`
- `COS_REGION`
- `AUTH_API_KEYS`
- `READINESS_TOKEN`
- `ADMIN_JWT_SECRET`
- `ADMIN_JWT_EXPIRE_MINUTES`
- `ALLOW_MOCK_PROVIDERS_IN_PROD`
- `EXTERNAL_PURCHASE_FEEDBACK_MODE`
- `REQUEST_MAX_BYTES`
- `UPLOAD_PROVIDER`
- `UPLOAD_DIR`
- `UPLOAD_PUBLIC_BASE_URL`
- `UPLOAD_MAX_BYTES`
- `UPLOAD_ALLOWED_TYPES`
- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOW_CREDENTIALS`
- `CORS_ALLOWED_METHODS`
- `CORS_ALLOWED_HEADERS`
- `DEMO_USER_REF`
- `FEEDBACK_DELAY_DAYS`
- `REVIEW_IMPORTED_BASE_WEIGHT`
- `REVIEW_VERIFIED_BASE_WEIGHT`
- `REVIEW_WEIGHT_CAP`
- `AI_LLM_MAX_CONCURRENCY`
- `AI_VISION_MAX_CONCURRENCY`
- `AI_SPEECH_MAX_CONCURRENCY`
- `AI_PROVIDER_TIMEOUT_SECONDS`
- `CAPACITY_RETRY_AFTER_SECONDS`
- `CHAT_RATE_LIMIT_PER_MINUTE`
- `VISION_RATE_LIMIT_PER_MINUTE`
- `SPEECH_RATE_LIMIT_PER_MINUTE`
- `UPLOAD_RATE_LIMIT_PER_MINUTE`
- `ANDROID_API_BASE_URL`
- `BUYWISE_BETA_TOKEN`

`LLM_PROVIDER` 支持 `mock`、`openai` 或 `openai-compatible`。非 mock provider 通过 OpenAI-compatible client 使用 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`，同时用于结构化理解用户需求和生成导购回复。LLM 不可用或返回非 JSON 意图结果时，后端会回退到规则抽取。

`EMBEDDING_PROVIDER` 支持 `mock`、`openai`、`openai-compatible` 或 `dashscope`。`mock` 使用稳定 hash 向量，保留给本地和测试；非 mock provider 使用 OpenAI-compatible embeddings API。`EMBEDDING_BASE_URL` 和 `EMBEDDING_API_KEY` 为空时分别回退到 `LLM_BASE_URL` 和 `LLM_API_KEY`，`EMBEDDING_MODEL` 控制实际 embedding 模型。

`VISION_PROVIDER` 支持 `mock`、`llm` 或 `dashscope`。非 mock 视觉 provider 使用 OpenAI-compatible 多模态聊天 API，演示路径优先使用 DashScope/Qwen-VL 兼容接口。如果视觉模型不同于聊天模型，设置 `VISION_BASE_URL`、`VISION_API_KEY` 和 `VISION_MODEL`；为空时回退到 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`。

`SPEECH_PROVIDER` 支持 `mock` 或 `tencent`。腾讯 ASR 使用上传后的公网音频 URL 调用 `SentenceRecognitionRequest.Url`，配置项包括 `TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`、`TENCENT_ASR_REGION` 和 `TENCENT_ASR_ENGINE_MODEL_TYPE`。`TENCENT_ASR_VOICE_FORMAT` 可覆盖发送给腾讯的音频格式；为空时后端从音频 URL 扩展名推断，并默认回退到 `wav`。

Closed beta 阶段默认 `SPEECH_PROVIDER=mock`，语音不作为发布门禁。`APP_ENV=prod` 且 `ALLOW_MOCK_PROVIDERS_IN_PROD=false` 时，`LLM_PROVIDER`、`VISION_PROVIDER` 和 `EMBEDDING_PROVIDER` 不能为 `mock`，但 `SPEECH_PROVIDER=mock` 允许。

`UPLOAD_PROVIDER` 支持 `local` 或 `cos`。本地上传保存到 `UPLOAD_DIR`；COS 上传使用 `TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`、`COS_BUCKET` 和 `COS_REGION`。

`AI_LLM_MAX_CONCURRENCY`、`AI_VISION_MAX_CONCURRENCY` 和 `AI_SPEECH_MAX_CONCURRENCY` 控制 closed beta 阶段进程内外部 AI provider 并发闸门。`AI_PROVIDER_TIMEOUT_SECONDS` 控制外部 provider 调用超时，`CAPACITY_RETRY_AFTER_SECONDS` 控制容量不足时返回的 `Retry-After`。`CHAT_RATE_LIMIT_PER_MINUTE`、`VISION_RATE_LIMIT_PER_MINUTE`、`SPEECH_RATE_LIMIT_PER_MINUTE` 和 `UPLOAD_RATE_LIMIT_PER_MINUTE` 控制入口限流；有 Bearer token 时按 API key subject 限流，否则按客户端 IP 限流。当前限流和容量保护只在单进程内生效。

当非 mock 视觉或语音 provider 接收 `/uploads/demo.wav` 这类相对上传路径时，必须配置 `UPLOAD_PUBLIC_BASE_URL`；后端会将 base URL 与相对路径拼接后发送给外部 provider。`APP_ENV=prod` 且视觉或语音 provider 非 mock 时，必须配置 `UPLOAD_PUBLIC_BASE_URL`，或使用 `UPLOAD_PROVIDER=cos` 返回公网对象 URL。

`ANDROID_API_BASE_URL` 用于 Android Gradle 构建配置，默认是 `http://10.0.2.2:8000`。Android closed beta 用户能力使用 `BUYWISE_BETA_TOKEN`，该 token 应在后端 `.env` 的 `AUTH_API_KEYS` 中配置，并具备 `upload:write`、`orders:read`、`orders:write`、`feedback:read` 和 `feedback:write` scope。`BUYWISE_UPLOAD_TOKEN` 仍可用于仅上传联调的本地演示，默认值为 `upload-token`。

`DEMO_USER_REF` 是未携带 Bearer token 时订单和已购评价使用的轻量用户标识。`FEEDBACK_DELAY_DAYS` 控制模拟订单收货后几天进入待评价列表，默认 7；演示收货后立即出现评价提示时可设为 0。`EXTERNAL_PURCHASE_FEEDBACK_MODE=immediate` 时，带 `external_platform` 的外部购买记录创建后直接进入已收货和待评价状态；`delayed` 时按 `FEEDBACK_DELAY_DAYS` 延迟。`REVIEW_IMPORTED_BASE_WEIGHT`、`REVIEW_VERIFIED_BASE_WEIGHT` 和 `REVIEW_WEIGHT_CAP` 控制评价权重公式中的导入评论基础权重、未来平台验真评价基础权重和单条权重上限。Closed beta 的外部购买记录使用 `purchase_evidence=buywise_recorded`，权重介于导入评论和未来平台验真评价之间。

## 安全

`AUTH_API_KEYS` 是用分号分隔的 API key 列表，格式为 `subject:token:scope1,scope2`。当前受保护 scope 包括 `/api/v1/upload` 使用的 `upload:write`，商品维护使用的 `products:write`，订单读取/写入使用的 `orders:read` 和 `orders:write`，模拟物流推进使用的 `orders:advance`，待评价和已购评价读取/写入使用的 `feedback:read` 和 `feedback:write`。

`READINESS_TOKEN` 保护 prod 下的 `/api/v1/ready`。调用方可使用 `Authorization: Bearer <token>` 或 `X-Readiness-Token: <token>`。不要把 readiness token 放入 Android beta 包，也不要复用普通用户 API key。

`ADMIN_JWT_SECRET` 用于内部后台管理员登录后签发 JWT access token。`ADMIN_JWT_EXPIRE_MINUTES` 控制 token 有效期，默认 480 分钟。管理员账号通过 `python -m app.scripts.create_admin_user --username <name> --password <password>` 创建；已有账号需要显式传 `--reset-password` 才会重置密码。dev/test 下如果数据库里还没有 `admin` 用户，后台允许使用内置账号 `admin` / `buywise-admin` 登录，方便本地首次打开后台；生产环境禁用该内置账号，且一旦创建了数据库中的 `admin` 用户，登录必须使用数据库密码。

订单、待评价提示和已购评价接口在 dev/test 阶段保留可选 Bearer token。请求携带有效 token 时使用 token subject 作为 `user_ref`；未携带 token 时使用 `DEMO_USER_REF`，用于 Android 合同流和演示环境。`APP_ENV=prod` 时，这些接口必须携带 Bearer token 并满足对应 scope；closed beta 使用受控 API key 身份，不等同于公网账号系统。

`REQUEST_MAX_BYTES` 限制 endpoint 处理前的 HTTP 请求体大小。`UPLOAD_MAX_BYTES` 是上传服务执行的单文件大小限制。

当 `APP_ENV=prod` 时，应用创建阶段会执行生产配置校验。生产环境必须关闭 debug，配置非占位 API key、readiness token、admin JWT secret、MySQL 密码和 secret，并使用显式 CORS origin。启用 credentials 时不得使用通配 CORS origin。`UPLOAD_PROVIDER=cos` 时必须配置 Tencent Secret、COS bucket 和 region。

## 本地运行覆盖项

- `BACKEND_PORT`
- `PROMETHEUS_PORT`
- `LOKI_PORT`
- `GRAFANA_PORT`
