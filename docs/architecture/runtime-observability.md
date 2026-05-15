# Runtime And Observability

BuyWise supports local Docker runtime, isolated PR environments, browser validation, and an optional observability stack.

## Docker Runtime

- Base compose file: `docker-compose.yml`
- Optional observability overlay: `docker-compose.observability.yml`
- Backend service listens on container port `8000`.
- MySQL service listens on container port `3306`.
- Host ports are controlled by `BACKEND_PORT` and `MYSQL_PORT`.

## Isolated PR Environments

Use `scripts/start_pr_env.ps1` and `scripts/stop_pr_env.ps1` to run separate worktrees and compose projects. Each project name gets independent containers, networks, and named volumes.

## Browser Validation

Use `scripts/browser_check.py` to validate `/api/v1/health`, open `/docs`, capture screenshots, and save a DOM snapshot through Playwright/CDP.

## Observability

The observability overlay adds Prometheus, Loki, Promtail, and Grafana. Promtail reads Docker logs and labels them with compose project and service metadata.
