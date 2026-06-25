# Closed Beta Runbook

This runbook covers the single-host closed beta deployment. It assumes one backend replica, MySQL in Docker Compose, Chroma persisted on the host, COS for durable uploads, and HTTPS terminated by a host reverse proxy. Short maintenance windows are acceptable during stage 1.

## Scope

- `APP_ENV=prod` with `APP_DEBUG=false`.
- One backend container and one MySQL container from `docker-compose.prod.yml`.
- MySQL is the source of truth for orders, feedback, and imported products.
- The product CSV is the rebuild source for the catalog; Chroma can be rebuilt from MySQL.
- `/api/v1/health` is public liveness. `/api/v1/ready` requires `READINESS_TOKEN` in prod.
- Observability Compose is recommended, but stage 1 release gates are logs, readiness, backup, index check, and smoke.

## Prepare Secrets

Copy `.env.prod.example` to `.env` on the host and replace every `change-me-*` value.

Required stage 1 settings:

- `APP_ENV=prod`
- `APP_DEBUG=false`
- `LLM_PROVIDER=openai` or `openai-compatible`
- `EMBEDDING_PROVIDER=openai-compatible` or `dashscope`
- `VISION_PROVIDER=llm` or `dashscope`
- `SPEECH_PROVIDER=mock`
- `UPLOAD_PROVIDER=cos`
- `EXTERNAL_PURCHASE_FEEDBACK_MODE=immediate`
- `READINESS_TOKEN=<strong-random-token>`
- `ALLOW_MOCK_PROVIDERS_IN_PROD=false`

Temporary recovery mode for demos before real SMS, vision, or ASR providers are stable:

- `ALLOW_MOCK_PROVIDERS_IN_PROD=true`
- `AUTH_OTP_MOCK_ENABLED=true`
- `VISION_PROVIDER=mock`
- `SPEECH_PROVIDER=mock`

In this mode, user OTP is the fixed mock code `123456`; do not use this mode for formal production traffic.

Use one `AUTH_API_KEYS` subject per tester or channel. Do not share a single beta token across all testers.

Recommended scopes:

- Tester token: `upload:write,orders:read,orders:write,feedback:read,feedback:write`
- Smoke token: `orders:read,orders:write,orders:advance,feedback:read,feedback:write`
- Admin token: `products:write`

Token rotation:

1. Append the new token to `AUTH_API_KEYS`.
2. Redeploy or restart backend.
3. Verify the new token works.
4. Remove the old token.
5. Redeploy or restart backend again.

## Start Compose

Build and start the single-host stack:

```powershell
docker compose -f docker-compose.prod.yml up -d --build
```

MySQL is not exposed on the host by the prod Compose file. Use `docker compose exec mysql ...` or an SSH tunnel for maintenance.

Run migrations:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.migrate_database
```

## HTTPS Reverse Proxy

Use Nginx as the stage 1 standard path. Backend should stay bound to `127.0.0.1:${BACKEND_PORT:-8000}` and Nginx should be the public entrypoint.

Example server block:

```nginx
server {
    listen 80;
    server_name api.buywise-beta.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.buywise-beta.example.com;

    ssl_certificate /etc/letsencrypt/live/api.buywise-beta.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.buywise-beta.example.com/privkey.pem;

    client_max_body_size 20m;

    location /api/v1/ai/chat/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_set_header Host $host;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_read_timeout 60s;
        proxy_set_header Host $host;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`client_max_body_size` must be at least `REQUEST_MAX_BYTES`.

## Catalog Import And Index

Use a real closed beta CSV. Do not mix demo seed data with the beta catalog. Keep the production file as a local ignored beta catalog CSV on the deployment host and do not commit it to Git; the repository only carries `data/beta-catalog.template.csv`.

Stage 1 catalog rules:

- Start with 5 categories and 10 real SKUs per category.
- Use manually curated public product pages; do not use crawler output as the source of truth.
- Treat `price`, `stock_status`, `rating`, and `sales` as an import-time snapshot.
- Use stable custom `sku` values such as `beta-keyboard-keynova-k75`; do not use platform item IDs as the only identity.
- Replace every template URL with a real `http(s)` product URL and a real image URL that opens without login.
- Fill `tags` and `suitable_scene` from `docs/reference/beta-catalog-taxonomy.md` so RAG recall stays predictable.

```powershell
python -m app.scripts.validate_beta_catalog --csv .\data\beta-catalog.csv
.\scripts\release_prepare.ps1 -ImportCsv .\data\beta-catalog.csv -RequireRealCatalog -BuildIndex -IndexMode rebuild -CheckIndex -ArtifactDir .\artifacts\release\$stamp
```

In Compose:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.import_products --csv /app/data/beta-catalog.csv --require-real-assets
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.build_vector_index --mode rebuild
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.check_vector_index
```

## Readiness

Runtime config summary:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.print_runtime_config_summary
```

Confirm the summary shows `app_env=prod`, `app_debug=false`, `allow_mock_providers_in_prod=false`, non-mock LLM/embedding/vision providers, the expected MySQL database, and the expected Chroma collection. The summary intentionally omits API keys, passwords, tokens, and other secrets.

HTTP readiness:

```powershell
curl.exe -H "X-Readiness-Token: <readiness-token>" https://api.buywise-beta.example.com/api/v1/ready
```

Detailed CLI readiness:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.readiness_check --expected-active-products 50
```

Readiness checks config, MySQL connectivity, active product count, Chroma collection access, and active product index coverage. Closed beta requires exactly 50 active SKUs; the HTTP `/ready` endpoint remains the generic runtime probe and does not enforce that catalog-size gate.

Save the index and readiness evidence with the release record:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.print_runtime_config_summary | Tee-Object ".\artifacts\runtime-config-$stamp.json"
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.check_vector_index | Tee-Object ".\artifacts\vector-index-$stamp.json"
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.readiness_check --expected-active-products 50 | Tee-Object ".\artifacts\readiness-$stamp.json"
```

## Smoke Test

Run the post-deploy verification entrypoint:

```powershell
.\scripts\closed_beta_verify.ps1 -BaseUrl https://api.buywise-beta.example.com -Token <smoke-token> -ReadinessToken <readiness-token> -ExpectedActiveProducts 50
```

Include real AI provider checks when the gateway and model keys are expected to be available:

```powershell
.\scripts\closed_beta_verify.ps1 -BaseUrl https://api.buywise-beta.example.com -Token <smoke-token> -ReadinessToken <readiness-token> -ExpectedActiveProducts 50 -IncludeAi
```

The smoke subject is intentionally retained for audit. Use `external_platform=smoke` and a `smoke-*` order ref so reports can filter it out.

## Backups

Create a backup before every deploy:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
docker compose -f docker-compose.prod.yml exec mysql sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > "backup-$stamp.sql"
python -m app.scripts.check_mysql_backup --path ".\backup-$stamp.sql" --min-bytes 1024 --max-age-hours 2 --artifact-json ".\artifacts\release\$stamp\backup-check.json"
```

The release record must reference the backup check artifact, not only the SQL filename.

Daily backup policy for stage 1:

- Keep 7 daily backups.
- Keep 4 weekly backups.
- Store a copy outside the host.

Chroma backup is optional. The standard recovery path is to rebuild Chroma from MySQL products after restore.

COS is not backed up by app scripts. Configure bucket lifecycle, versioning if needed, and least-privilege keys in Tencent Cloud.

## Restore

Restore MySQL from a selected backup:

```powershell
Get-Content .\backup-20260525-153000.sql | docker compose -f docker-compose.prod.yml exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
```

Then rebuild and verify Chroma:

```powershell
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.build_vector_index --mode rebuild
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.check_vector_index
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.readiness_check --expected-active-products 50
```

Run smoke after restore.

## Rollback

If only the backend image is bad:

1. Switch to the previous image tag or commit.
2. Restart backend.
3. Run readiness and smoke.

If a migration or catalog import polluted data:

1. Stop backend.
2. Restore the release backup.
3. Rebuild Chroma.
4. Start backend.
5. Run readiness and smoke.

Do not restore MySQL for a simple application image rollback unless data was changed incorrectly.

## Failure Checks

- `401` on `/ready`: wrong or missing `READINESS_TOKEN`.
- `503` on `/ready`: run `python -m app.scripts.readiness_check --expected-active-products 50` inside backend for details.
- Empty products: rerun import with `--require-real-assets`.
- RAG returns no items: rerun `build_vector_index --mode rebuild`, then `check_vector_index`.
- Upload provider fails: verify COS bucket, region, Tencent keys, and bucket policy.
- AI degraded: verify LLM/Vision base URL, model, API key, concurrency, and provider timeout.
