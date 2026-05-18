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

## Local Runtime Overrides

- `BACKEND_PORT`
- `PROMETHEUS_PORT`
- `LOKI_PORT`
- `GRAFANA_PORT`
