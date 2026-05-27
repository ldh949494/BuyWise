# 脚本参考

## 验证

- `scripts/auto_validate.ps1`：仓库提交前和 CI 验证入口。它会运行文档校验、provider lint、仓库 lint、熵债校验、后端 smoke check、使用仓库内 basetemp 且禁用 cache 的 pytest，并可选择构建 Android。
- `scripts/release_check.ps1`：发版前聚合验证入口。默认调用 `auto_validate.ps1`、Android lint 和 Android debug build；传入 `-CheckIndex` 时运行 `app.scripts.check_vector_index`，传入 `-Token` 与 `-ReadinessToken` 时运行 closed beta readiness 和 smoke。可用 `-ExpectedActiveProducts <count>` 把固定目录规模门禁传给 readiness；可用 `-SkipAndroidBuild`、`-SkipAndroidAnalyze` 和 `-SkipDependencyInstall` 控制本地耗时。
- `scripts/validate_docs.py`：校验 `AGENTS.md` 和 `docs/`。
- `scripts/validate_providers.py`：校验后端模块是否通过统一 Provider 入口访问横切能力。
- `scripts/validate_repo_lint.py`：自定义仓库 linter，覆盖结构化日志、命名、文件大小和导入边界。
- `scripts/validate_entropy.py`：根据 `docs/entropy/baseline.json` 校验黄金原则熵债规则。
- `scripts/entropy_gc.py`：在 `artifacts/entropy-gc/` 下生成只读熵债清理报告。
- `scripts/entropy_cleanup_agent.py`：通过 GitHub Models 执行一个低风险熵债清理，供后台清理流程使用。

## 依赖文件

- `requirements.in`：生产直接依赖输入。
- `requirements.txt`：Docker 和运行时设置使用的生产锁定依赖文件。
- `requirements-dev.in`：叠加在生产依赖上的开发依赖输入。
- `requirements-dev.txt`：`scripts/auto_validate.ps1` 使用的开发锁定依赖文件。
- 有意修改依赖输入后，使用 `pip-compile requirements.in` 和 `pip-compile requirements-dev.in` 重新生成锁定文件。

## 运行时

- `scripts/start_backend.ps1`：本机开发后端启动脚本。它加载 UTF-8 设置，执行数据库迁移，并启动 Uvicorn。如果 `.env` 中的 `MYSQL_HOST=mysql`，会在当前本机进程中使用 `127.0.0.1` 连接 Docker 暴露到宿主机的 MySQL。可用 `-Port <port>` 切换端口、`-NoReload` 关闭 reload、`-SkipMigration` 跳过迁移。
- `scripts/release_prepare.ps1`：发版或首次部署前的显式准备脚本。默认只执行数据库迁移；使用 `-SeedProfile android-contract|demo` 写入确定性 seed 数据，使用 `-ImportCsv <path>` 导入商品 CSV，使用 `-RequireRealCatalog` 对 closed beta 真实目录启用真实商品链接、图片和库存字段校验，使用 `-BuildIndex -IndexMode upsert|rebuild` 构建向量索引，使用 `-CheckIndex` 检查索引健康。`-SeedProfile` 和 `-ImportCsv` 不能同时使用，避免混合演示数据和外部商品目录。启用 `-RequireRealCatalog` 时必须同时传入 `-BuildIndex -IndexMode rebuild -CheckIndex`。
- `scripts/start_pr_env.ps1`：创建或复用隔离 worktree，并用指定 project name 启动 Docker Compose。
- `scripts/stop_pr_env.ps1`：停止隔离 compose project，可选择删除 volume 或 worktree。
- `scripts/start_demo.ps1`：本地演示启动脚本。它检查 `.env` 的 LLM 配置，执行迁移、`seed_products --profile demo`、向量索引构建，并启动 Uvicorn。可用 `-SkipIndex` 跳过索引、`-Port <port>` 切换端口、`-AllowMockLlm` 做离线 smoke。
- `scripts/browser_check.py`：通过 Playwright/CDP 验证运行中的后端。
- `scripts/demo_api_check.py`：验证演示备用 API 路径，依次请求 health、商品列表、商品对比和 AI 导购，并确认固定演示问题首推 demo 键盘。
- `scripts/closed_beta_smoke.py`：closed beta HTTP smoke。依次检查 health、ready、商品列表、RAG search、外部购买记录、待评价和提交评价；使用 `--include-ai` 时额外验证真实导购返回商品且未降级。
- `scripts/closed_beta_verify.ps1`：发布后验证薄入口。先打印非敏感 runtime config summary，再运行 `app.scripts.readiness_check` 和 `scripts/closed_beta_smoke.py`；可用 `-ExpectedActiveProducts <count>` 检查 active 商品数，可用 `-IncludeAi` 打开真实 AI 检查。

## 数据与维护

- `app.scripts.migrate_database`：对配置的数据库执行 Alembic 迁移。
- `app.scripts.create_tables`：兼容 wrapper，内部执行 Alembic 迁移。
- `app.scripts.seed_products`：upsert 确定性商品种子数据。默认 profile 是 `android-contract`，用于 Android 合同流；演示时使用 `python -m app.scripts.seed_products --profile demo` 写入更适合固定提问和商品卡片展示的 demo 数据。旧 seed 数据如果曾以乱码写入，重新运行该脚本即可按固定商品 ID 更新。
- `app.scripts.import_products`：从 CSV 导入商品。CSV 必须包含 `sku`、`name`、`category`、`price`、`tags`；脚本先整批校验，再按 `sku` upsert，输出 `inserted`、`updated`、`failed`。Closed beta 真实目录使用 `--require-real-assets`，要求每行包含真实 `product_url`、真实图片 URL，以及 `stock` 或 `stock_status`。
- `data/beta-catalog.template.csv`：closed beta 真实商品目录模板。真实目录文件使用本地忽略的 beta catalog CSV，不提交到 Git。第一版目录建议人工维护 5 个类目、每类 10 个真实 SKU；`sku` 使用自定义稳定值，动态字段按导入当天人工快照填写。推荐字段顺序为 `sku,name,category,brand,price,original_price,platform,product_url,image_url,image_urls,rating,sales,description,specs,tags,suitable_scene,stock,stock_status,review_summary`。`tags`、`suitable_scene`、`image_urls` 必须是 JSON 数组，`specs` 必须是 JSON 对象。`tags` 和 `suitable_scene` 从 `docs/reference/beta-catalog-taxonomy.md` 选择，避免同义词漂移。模板中的 URL 只能作为占位，正式导入前必须替换为可无登录打开的真实商品页和图片 URL。
- `app.scripts.validate_beta_catalog`：只读校验 closed beta 真实商品 CSV，不写数据库。示例：`python -m app.scripts.validate_beta_catalog --csv .\data\beta-catalog.csv`。它复用导入脚本的真实 URL、图片、库存和基础 JSON 校验，并额外检查 5 个固定类目、每类 10 个 SKU、`beta-...` SKU 命名、模板表头、`review_summary`、`specs` JSON 对象，以及 `tags` 和 `suitable_scene` 是否来自 `docs/reference/beta-catalog-taxonomy.md`。
- 推荐演示问题：`帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高`。demo profile 下该问题应首推 `Campus75 三模静音机械键盘`。
- `scripts/set_utf8.ps1`：将 PowerShell 和 Python 进程编码设置为 UTF-8。如果终端查看 seed 数据时出现乱码，先点加载它：`. .\scripts\set_utf8.ps1`。
- `app.scripts.build_vector_index`：重建或增量 upsert 持久化 ChromaDB 商品索引。`--mode rebuild` 会重置完整 collection，`--mode upsert` 会全量 upsert 但不重置，`--mode upsert --product-id <id>` 只更新指定商品。
- `app.scripts.check_vector_index`：输出商品向量索引健康 JSON，包括 collection count、DB 商品数、缺失索引 ID 和陈旧索引 ID。可传入 `--profile android-contract` 或 `--profile demo` 校验固定 seed 商品 ID；索引缺失或陈旧时返回非 0 exit code。
- `app.scripts.readiness_check`：输出详细 readiness JSON 并在失败时返回非 0 exit code。检查 prod 配置、MySQL、商品数量、Chroma collection 和 active 商品索引覆盖。可传入 `--expected-active-products <count>`，用于 closed beta 等固定目录规模发布门禁。
- `app.scripts.print_runtime_config_summary`：输出非敏感运行配置摘要，用于确认实际加载的环境、provider、MySQL 和 Chroma 配置；不会打印 API key、密码或 token。
- `app.scripts.cleanup_uploads`：清理本地 `UPLOAD_DIR` 下超过 TTL 的上传文件。示例：`python -m app.scripts.cleanup_uploads --max-age-hours 24 --dry-run`。仅清理允许扩展名的普通文件；COS 上传的生命周期应在 bucket 上配置。
- `app.scripts.evaluate_rag`：运行小型 RAG 购物需求评测集，并输出 `recall@k`、`top1_accuracy`、`mrr@k`、失败案例和 case-level diagnostics。使用 `python -m app.scripts.evaluate_rag`；传入 `--profile android-contract|demo|beta-fixture` 可选择 Android 合同、演示或 beta fixture 评测集，传入 `--retrieval fallback|vector` 可选择数据库 fallback 或临时重建 Chroma 向量索引，传入 `--output-json <path>` 可保存报告。
- `scripts/init_db.py`：数据库初始化辅助脚本，执行 Alembic 迁移。
- `scripts/ai_update_readme.py`：GitHub Actions 使用的 AI 辅助 README 更新脚本。
- `scripts/doc_gardening.py`：AI 辅助仓库记忆维护报告。默认只写报告；使用 `--apply` 时才会编辑 `AGENTS.md`、README 或 `docs/`。

后台维护任务保持为手动或外部调度脚本，不在 FastAPI 进程内启动常驻 scheduler。生产环境可用 cron、Windows Task Scheduler、CI/CD scheduled job 或容器平台 CronJob 定期执行上传清理和索引健康检查，避免多副本应用进程重复执行维护任务。
