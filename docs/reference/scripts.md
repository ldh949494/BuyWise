# 脚本参考

## 验证

- `scripts/auto_validate.ps1`：仓库提交前和 CI 验证入口。它会运行文档校验、provider lint、仓库 lint、熵债校验、后端 smoke check、使用仓库内 basetemp 且禁用 cache 的 pytest，并可选择构建 Android。
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

- `scripts/start_pr_env.ps1`：创建或复用隔离 worktree，并用指定 project name 启动 Docker Compose。
- `scripts/stop_pr_env.ps1`：停止隔离 compose project，可选择删除 volume 或 worktree。
- `scripts/start_demo.ps1`：本地演示启动脚本。它检查 `.env` 的 LLM 配置，执行迁移、`seed_products --profile demo`、向量索引构建，并启动 Uvicorn。可用 `-SkipIndex` 跳过索引、`-Port <port>` 切换端口、`-AllowMockLlm` 做离线 smoke。
- `scripts/browser_check.py`：通过 Playwright/CDP 验证运行中的后端。
- `scripts/demo_api_check.py`：验证演示备用 API 路径，依次请求 health、商品列表、商品对比和 AI 导购，并确认固定演示问题首推 demo 键盘。

## 数据与维护

- `app.scripts.migrate_database`：对配置的数据库执行 Alembic 迁移。
- `app.scripts.create_tables`：兼容 wrapper，内部执行 Alembic 迁移。
- `app.scripts.seed_products`：upsert 确定性商品种子数据。默认 profile 是 `android-contract`，用于 Android 合同流；演示时使用 `python -m app.scripts.seed_products --profile demo` 写入更适合固定提问和商品卡片展示的 demo 数据。旧 seed 数据如果曾以乱码写入，重新运行该脚本即可按固定商品 ID 更新。
- `app.scripts.import_products`：从 CSV 导入商品。CSV 必须包含 `sku`、`name`、`category`、`price`、`tags`；脚本先整批校验，再按 `sku` upsert，输出 `inserted`、`updated`、`failed`。
- 推荐演示问题：`帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高`。demo profile 下该问题应首推 `Campus75 三模静音机械键盘`。
- `scripts/set_utf8.ps1`：将 PowerShell 和 Python 进程编码设置为 UTF-8。如果终端查看 seed 数据时出现乱码，先点加载它：`. .\scripts\set_utf8.ps1`。
- `app.scripts.build_vector_index`：重建或增量 upsert 持久化 ChromaDB 商品索引。`--mode rebuild` 会重置完整 collection，`--mode upsert` 会全量 upsert 但不重置，`--mode upsert --product-id <id>` 只更新指定商品。
- `app.scripts.check_vector_index`：输出商品向量索引健康 JSON，包括 collection count、DB 商品数、缺失索引 ID 和陈旧索引 ID。可传入 `--profile android-contract` 或 `--profile demo` 校验固定 seed 商品 ID。
- `app.scripts.evaluate_rag`：运行小型 RAG 购物需求评测集，并输出 `recall@k`、`top1_accuracy`、`mrr@k` 和失败案例。使用 `python -m app.scripts.evaluate_rag`；传入 `--profile android-contract|demo` 可选择 Android 合同或演示评测集，传入 `--output-json <path>` 可保存报告。
- `scripts/init_db.py`：数据库初始化辅助脚本，执行 Alembic 迁移。
- `scripts/ai_update_readme.py`：GitHub Actions 使用的 AI 辅助 README 更新脚本。
- `scripts/doc_gardening.py`：AI 辅助仓库记忆维护报告。默认只写报告；使用 `--apply` 时才会编辑 `AGENTS.md`、README 或 `docs/`。
