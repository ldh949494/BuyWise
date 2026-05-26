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

发版或首次部署前先显式准备数据库和可选数据资产：

```powershell
.\scripts\release_prepare.ps1
.\scripts\release_prepare.ps1 -ImportCsv .\data\products.csv -BuildIndex
.\scripts\release_prepare.ps1 -SeedProfile demo -BuildIndex -CheckIndex
```

`release_prepare.ps1` 默认只执行 Alembic 迁移。商品 seed、CSV 导入、向量索引构建和索引检查都必须显式开启；应用容器启动时不自动写入演示数据，也不自动重建索引。

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

## 业务指标

`/metrics` 暴露默认 HTTP 指标和 BuyWise 业务指标。业务指标只使用低基数标签，禁止把 `session_id`、用户输入、商品 ID 或 query 放入 Prometheus label；这些细节保留在结构化日志中。

当前业务指标：

- `buywise_chat_latency_seconds`：聊天端到端耗时，标签 `mode=json|sse`、`outcome=success|error|degraded|clarify`。
- `buywise_llm_failures_total`：LLM 失败计数，标签 `operation` 和 `reason`。
- `buywise_rag_fallback_total`：RAG fallback 计数，标签 `entrypoint=rag_search|chat` 和 `stage`。
- `buywise_rag_empty_results_total`：RAG 空结果计数，标签 `entrypoint` 和 `source`。
- `buywise_upload_failures_total`：上传失败计数，标签 `reason`。
- `buywise_order_created_total`、`buywise_feedback_prompted_total`、`buywise_feedback_submit_success_total`：订单到反馈漏斗计数。
- `buywise_feedback_submit_failures_total`：反馈提交失败计数，标签 `reason`。

订单到反馈转化率口径为 `buywise_feedback_submit_success_total / buywise_feedback_prompted_total`。上传和反馈提交失败率先按服务端响应失败口径统计，客户端取消、网络错误和超时由客户端日志或埋点补充。

## 后台维护

后台维护任务采用脚本加外部调度，不在 FastAPI 进程内运行常驻 scheduler。上传 TTL 清理使用 `python -m app.scripts.cleanup_uploads --max-age-hours 24`；向量索引健康检查使用 `python -m app.scripts.check_vector_index`，必要时再运行 `python -m app.scripts.build_vector_index --mode upsert` 或 `--mode rebuild`。生产调度由 cron、Windows Task Scheduler、CI/CD scheduled job 或容器平台 CronJob 承载。

## 验证

提交前运行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

发版前运行：

```powershell
.\scripts\release_check.ps1 -SkipDependencyInstall -CheckIndex -IndexProfile demo
```
