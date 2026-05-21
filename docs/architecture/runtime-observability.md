# 运行时与可观测性

BuyWise 后端可以直接用 Uvicorn 运行，也可以通过 Docker Compose 启动后端、MySQL 和可观测组件。

## 本地运行

常用后端启动命令：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Docker 入口：

```powershell
docker compose up --build
```

## PR 环境

`scripts/start_pr_env.ps1` 会创建或复用隔离 worktree，并使用独立 Compose project name 启动后端和 MySQL。`scripts/stop_pr_env.ps1` 用于停止环境，可选择删除 volume 和 worktree。

## 可观测组件

`docker-compose.observability.yml` 提供 Prometheus、Loki、Promtail 和 Grafana。带可观测能力启动 PR 环境：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

默认端口：

- 后端：`http://127.0.0.1:8123`
- Prometheus：`http://127.0.0.1:9090`
- Loki：`http://127.0.0.1:3100`
- Grafana：`http://127.0.0.1:3000`

## 日志和错误

后端通过 provider 配置结构化日志和全局错误处理。请求中的 `X-Request-ID` 会进入响应和日志，方便前后端联合排查。

## 验证

提交前运行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```
