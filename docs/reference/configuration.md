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
- `ANDROID_API_BASE_URL`

`LLM_PROVIDER` 支持 `mock`、`openai` 或 `openai-compatible`。非 mock provider 通过 OpenAI-compatible client 使用 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`，同时用于结构化理解用户需求和生成导购回复。LLM 不可用或返回非 JSON 意图结果时，后端会回退到规则抽取。

`VISION_PROVIDER` 支持 `mock`、`llm` 或 `dashscope`。非 mock 视觉 provider 使用 OpenAI-compatible 多模态聊天 API。如果视觉模型不同于聊天模型，设置 `VISION_BASE_URL`、`VISION_API_KEY` 和 `VISION_MODEL`；为空时回退到 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`。

`SPEECH_PROVIDER` 支持 `mock` 或 `tencent`。腾讯 ASR 使用 `TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`、`TENCENT_ASR_REGION` 和 `TENCENT_ASR_ENGINE_MODEL_TYPE`。`TENCENT_ASR_VOICE_FORMAT` 可覆盖发送给腾讯的音频格式；为空时后端从音频 URL 扩展名推断，并默认回退到 `wav`。

`UPLOAD_PROVIDER` 支持 `local` 或 `cos`。本地上传保存到 `UPLOAD_DIR`；COS 上传使用 `TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`、`COS_BUCKET` 和 `COS_REGION`。

当非 mock 视觉或语音 provider 接收 `/uploads/demo.wav` 这类相对上传路径时，必须配置 `UPLOAD_PUBLIC_BASE_URL`；后端会将 base URL 与相对路径拼接后发送给外部 provider。

`ANDROID_API_BASE_URL` 用于 Android Gradle 构建配置，默认是 `http://10.0.2.2:8000`。

## 安全

`AUTH_API_KEYS` 是用分号分隔的 API key 列表，格式为 `subject:token:scope1,scope2`。当前受保护 scope 包括 `/api/v1/upload` 使用的 `upload:write`，以及 `POST /api/v1/products` 使用的 `products:write`。

`REQUEST_MAX_BYTES` 限制 endpoint 处理前的 HTTP 请求体大小。`UPLOAD_MAX_BYTES` 是上传服务执行的单文件大小限制。

当 `APP_ENV=prod` 时，应用创建阶段会执行生产配置校验。生产环境必须关闭 debug，配置非占位 API key 和 secret，并使用显式 CORS origin。启用 credentials 时不得使用通配 CORS origin。

## 本地运行覆盖项

- `BACKEND_PORT`
- `PROMETHEUS_PORT`
- `LOKI_PORT`
- `GRAFANA_PORT`
