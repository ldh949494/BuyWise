# 计划：后端框架工程化加固

## 目标

把 BuyWise 后端从功能闭环稳定推进到更接近生产级工程实现。重点不是新增业务能力，而是收敛事务、依赖、配置、外部调用韧性、发布门禁和可观测治理，使后续导购、RAG、多模态、订单反馈和 closed beta 运维可以继续扩展而不明显增加框架债。

成功标准：

- 后端事务边界、依赖生命周期、配置分组和横切 provider 职责清晰。
- 外部依赖失败、降级、重试、熔断、健康检查和指标口径统一。
- RAG/AI 质量、真实依赖 smoke 和 OpenAPI contract 能进入发布门禁。
- 后台脚本类任务有可审计、可复跑、可留存的执行结果。

## 任务

- [x] 统一事务边界，引入 Unit of Work 或 Transaction Manager。
  - 当前问题：多个 service 自行 `commit()` / `rollback()`，跨用例事务和补偿难统一。
  - 验收标准：业务 service 不直接提交事务；API use case、脚本入口或统一事务包装器负责提交和回滚；已有订单、评价、商品、聊天写入测试全部通过。
  - 完成记录：新增 `app.core.transaction.unit_of_work`，商品、订单、评价、聊天和管理员写入路径已收敛到统一事务 helper。脚本批处理入口仍保留显式事务边界，作为后续作业治理任务的一部分继续收敛。

- [x] 建立强类型应用 composition root，替代松散的 `app.state` 字典依赖缓存。
  - 当前问题：依赖生命周期和类型约束弱，外部 client、RAG pipeline、vector store 的初始化、关闭和健康状态不集中。
  - 验收标准：应用启动时构建明确的依赖容器；shutdown 时释放可关闭资源；readiness 能引用容器内依赖状态；测试仍可替换单个依赖。
  - 状态：已完成。
  - 进展记录：新增 typed `AppContainer`，应用 lifespan 构建容器并在 shutdown 调用 `close()`；FastAPI dependencies 从容器属性取 LLM、RAG、vector store、chat、compare、vision 和 speech 服务，不再使用松散 dict cache。
  - 完成记录：容器注册从 `app.state` 动态缓存改为 typed app-container registry；新增 `AppContainerBuilder` 支持容器级单依赖替换；readiness service 进入容器并复用容器内 session factory 和 Chroma product store；HTTP readiness、admin ops summary 和 readiness CLI 均通过 composition root 获取 readiness 依赖。

- [x] 明确同步数据库在 async HTTP 链路中的阻塞边界。
  - 当前问题：同步 SQLAlchemy session 混在 FastAPI async 链路里，容量模型依赖线程池和连接池行为。
  - 验收标准：补充连接池、statement timeout、阻塞调用边界和容量说明；高成本路径使用明确的线程池封装或评估 async SQLAlchemy 迁移方案。
  - 完成记录：新增 `docs/design/sync-db-blocking-boundary.md`，明确当前版本保留同步 SQLAlchemy、async endpoint 高成本同步 DB/向量路径使用 `run_blocking_io`、连接池和 statement timeout 的容量约束，以及 async SQLAlchemy 的后续评估条件。

- [x] 拆分配置域，降低 `Settings` 大对象膨胀。
  - 当前问题：数据库、AI、上传、鉴权、CORS、限流、反馈、readiness 等配置集中在一个类里。
  - 验收标准：拆出数据库、AI、上传、安全、流量控制等配置分组；保持现有环境变量兼容；生产配置校验按域组织；配置测试覆盖默认值和 prod 错误。
  - 完成记录：新增 `app.core.settings_groups`，提供 `database`、`ai`、`upload`、`security` 和 `traffic` 五个只读配置域；现有环境变量和 `settings.xxx` 调用保持兼容。

- [x] 拆分 provider 实现，保留统一 provider 入口。
  - 当前问题：logging、telemetry、middleware、error、auth 入口集中在 `providers.py`，继续扩展会形成横切大文件。
  - 验收标准：provider registry 仍是统一访问点；具体 provider 分模块实现；`validate_providers.py` 继续禁止绕过 provider 边界。
  - 完成记录：`providers.py` 已收敛为 registry 和统一出口；logging、telemetry、middleware 分别拆到独立 provider 实现模块；`validate_providers.py` 已同步允许这些实现模块直接访问底层横切依赖。

- [x] 建立统一外部调用 resilience policy。
  - 当前问题：LLM、embedding、vision、speech、COS、Chroma 的 timeout、错误分类、重试和降级策略分散。
  - 验收标准：统一定义 timeout、retry、circuit breaker、错误分类和 degraded reason；高成本外部调用全部复用；指标可区分 capacity、timeout、provider_error、configuration_error。
  - 状态：已完成。
  - 进展记录：新增 `app.core.resilience`，LLM、embedding、vision、speech 已复用统一 provider timeout 和错误分类；测试覆盖 capacity、timeout、configuration_error、provider_error 分类。
  - 完成记录：`app.core.resilience` 新增统一执行器、retry、进程内 circuit breaker 和 provider failure 指标；LLM、embedding、vision、speech、COS 与 Chroma 调用均通过统一 policy 执行，指标统一按 `provider`、`operation`、`reason` 记录 capacity、timeout、provider_error 和 configuration_error。

- [x] 将 RAG/AI 评测阈值纳入 release gate。
  - 当前问题：`evaluate_rag` 和索引检查可运行，但质量阈值尚未成为强发布门禁。
  - 验收标准：`release_check.ps1` 可配置并执行 RAG eval 阈值；报告包含 recall、top1、MRR、fallback rate、empty result rate；低于阈值时 release check 失败。
  - 完成记录：新增 `app.scripts.rag_eval_gate`，复用现有 RAG eval 并补充 `fallback_rate`、`empty_result_rate` 和阈值失败原因；`release_check.ps1` 新增 `-RunRagEval` 及可配置 profile、retrieval、top_k、质量阈值和 JSON artifact 参数。

- [x] 增加真实依赖 smoke 分层。
  - 当前问题：pytest 大量使用 SQLite、fake provider 和 in-memory 环境，不能完全代表部署运行。
  - 验收标准：定义 unit、integration、release 三档测试；integration 覆盖 MySQL、Chroma、mock external providers；release 覆盖真实或沙箱 AI/COS/readiness/smoke。
  - 状态：已完成。
  - 完成记录：`pytest.ini` marker 和 `scripts/test_matrix.ps1` 已定义 unit、integration、release 三档；integration 覆盖 Chroma、MySQL 兼容路径和 mock external provider；新增 `app.scripts.real_dependency_smoke`，MySQL 真连接 smoke 要求 MySQL dialect 并执行 `SELECT 1`，COS smoke 使用 `head_bucket` 或只读 list fallback 检查 bucket 可访问性且不上传对象；`release_check.ps1 -RunRealDependencySmoke` 和 `test_matrix.ps1 -Tier release -RunRealDependencySmoke` 已接入 release 层。

- [x] 增加 OpenAPI contract snapshot 和 diff 门禁。
  - 当前问题：Android contract 测试覆盖重点响应，但公共 API schema 变化缺少整体快照对比。
  - 验收标准：生成并提交 OpenAPI snapshot；schema diff 在 CI 或 release check 中可运行；破坏性变化需要显式确认并同步文档。
  - 完成记录：新增 `docs/reference/openapi.snapshot.json` 和 `app.scripts.openapi_contract`，支持 `--write` 生成规范化快照与默认 diff 检查；`release_check.ps1 -CheckOpenApiContract` 可作为发布门禁执行。

- [x] 系统化后台作业执行结果。
  - 当前问题：catalog import、index rebuild、COS image migration、backup check 等依赖脚本输出，缺少统一作业记录。
  - 验收标准：脚本输出机器可读 artifact；记录输入、输出、耗时、结果、错误原因和操作者或执行环境；closed beta release 记录能引用这些 artifact。
  - 状态：已完成。
  - 完成记录：`app.scripts.job_artifacts.run_job_with_artifact` 统一记录 job 名称、输入、输出、耗时、状态、错误原因、环境和操作者；`import_products`、`build_vector_index` 和 `migrate_product_images_to_cos` 已支持 `--artifact-json`。新增 `app.scripts.check_mysql_backup` 记录备份证据校验 artifact；`release_prepare.ps1 -ArtifactDir/-ArtifactJson` 会输出聚合 artifact，并为导入和索引构建写入子 artifact；closed beta release checklist 已要求强制引用这些 artifact。

- [x] 规划安全模型升级路径。
  - 当前问题：受控 API key 适合 closed beta，但不适合公网用户体系。
  - 验收标准：保留当前 API key closed beta 能力；补充 OIDC/JWT、token rotation、用户主体、admin audit log 的迁移设计；不在当前版本引入真实购物车和支付。
  - 完成记录：新增 `docs/design/security-model-upgrade.md`，明确阶段化保留 closed beta API key、引入统一 Principal、OIDC/JWT、token rotation、admin audit log，并继续排除当前版本真实购物车、支付、地址簿和真实结算。

- [x] 将可观测性升级为 SLO。
  - 当前问题：已有 metrics，但尚未定义发布和运维判断阈值。
  - 验收标准：定义 chat p95、RAG empty rate、RAG fallback rate、LLM degraded rate、upload failure rate、feedback submit failure rate 等 SLO；release 记录包含与上一版本对比。
  - 完成记录：新增 `docs/operations/slo.md`，定义 chat p95、RAG empty/fallback rate、LLM degraded rate、upload failure rate、feedback submit failure rate、order-to-feedback conversion 的闭测阈值、来源和处置规则；`docs/operations/release-checklist.md` 已要求记录并对比上一版本 SLO snapshot。

## 优先级

第一批：

- [x] Unit of Work / Transaction Manager。
- [x] 配置域拆分和 provider 拆分。
- [x] 统一 resilience policy。
- [x] RAG/AI eval 阈值接入 release gate。

第二批：

- [x] 强类型 composition root。
- [x] 真实依赖 smoke 分层。
- [x] OpenAPI contract snapshot。
- [x] 后台作业 artifact。
第三批：

- [x] 同步数据库阻塞边界或 async SQLAlchemy 迁移评估。
- [x] 安全模型升级设计。
- [x] SLO 与发布对比报告。

## 验证

- `python scripts/validate_docs.py`
- `python scripts/validate_providers.py`
- `python scripts/validate_repo_lint.py`
- `python scripts/validate_entropy.py`
- `.\\.venv\\Scripts\\python.exe -m pytest`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`
- 完成 release gate 相关任务后，补跑 `.\scripts\release_check.ps1` 对应新参数。

## 完成记录

完成后记录实际落地内容，并将本文件移动到 `docs/plans/archive/`。
