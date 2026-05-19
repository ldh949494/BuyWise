# Configuration Reference

Environment examples live in `.env.dev.example`, `.env.test.example`, and `.env.prod.example`.

## Application

- `APP_NAME`
- `APP_ENV`
- `APP_PORT`
- `APP_DEBUG`
- `API_V1_PREFIX`
- `LOG_LEVEL`

## Database

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `SQLALCHEMY_ECHO`

Alembic uses these same settings through `app.core.config.Settings.database_url`.

## AI And Storage

- `CHROMA_PERSIST_DIR`
- `CHROMA_PRODUCT_COLLECTION`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `EMBEDDING_MODEL`
- `LLM_PROVIDER`
- `TENCENT_SECRET_ID`
- `TENCENT_SECRET_KEY`
- `COS_BUCKET`
- `COS_REGION`
- `AUTH_API_KEYS`
- `REQUEST_MAX_BYTES`
- `UPLOAD_DIR`
- `UPLOAD_MAX_BYTES`
- `UPLOAD_ALLOWED_TYPES`
- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOW_CREDENTIALS`
- `CORS_ALLOWED_METHODS`
- `CORS_ALLOWED_HEADERS`

`LLM_PROVIDER` accepts `mock`, `openai`, or `openai-compatible`. Non-mock providers use `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` through the OpenAI-compatible client.

## Security

`AUTH_API_KEYS` is a semicolon-separated list of API keys in `subject:token:scope1,scope2` format. The first protected scopes are `upload:write` for `/api/v1/upload` and `products:write` for `POST /api/v1/products`.

`REQUEST_MAX_BYTES` limits the HTTP request body size before endpoint handling. `UPLOAD_MAX_BYTES` remains the per-file upload limit enforced by the upload service.

Production configuration validation runs during app creation when `APP_ENV=prod`. Production must disable debug mode, configure non-placeholder API keys and secrets, and use explicit CORS origins. Do not combine wildcard CORS origins with credentials.

## Local Runtime Overrides

- `BACKEND_PORT`
- `PROMETHEUS_PORT`
- `LOKI_PORT`
- `GRAFANA_PORT`
