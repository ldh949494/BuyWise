# 当前计划

## 目标

保持 BuyWise closed beta 工程底座可维护：公共契约、运行配置、Android 行为、脚本参考和运维文档需要跟随代码同步；发布前再按 release checklist 执行完整门禁。

## 活跃任务

- [ ] 公共端点、环境变量、脚本、Android 行为或部署流程变化时，同步参考文档和架构文档。
- [ ] 修改 `docs/` 或 `AGENTS.md` 后运行 `python scripts/validate_docs.py`。
- [ ] 重大结构变化后运行 `python scripts/doc_gardening.py` 并人工审阅报告。
- [ ] closed beta 发布前按 `docs/operations/release-checklist.md` 运行后端、Android、数据导入、索引健康、readiness、RAG gate、OpenAPI contract 和真实依赖 smoke 验证。

## 已完成记录

- 后端已按 `docs/design/p1-order-feedback-loop.md` 实现交易影子模型和反馈闭环：`orders`、`order_items`、扩展 `reviews`、订单状态推进、待评价提示、已购评价提交/更新/撤回、归属校验和反馈权重聚合。
- 已购反馈信号已接入推荐、对比、商品详情和聊天分析，并保持预算、品类、库存、场景等主约束优先。
- 商品维护、RAG 演示质量、多模态 provider、上传清理、release prepare、脚本参考和主要 API/config 参考已同步到实现。
- P1 认证边界保持轻量：订单、反馈和已购评价保留可选 Bearer token，真实生产用户体系后续迁移。
- 后台维护策略保持脚本加外部调度，不在 FastAPI 进程内引入常驻 scheduler。
- Android 已有部分闭环：商品详情记录购买、首页待评价提示和一键提交固定内容评价。
- 已完成 closed beta 方向决策：不新增 `APP_ENV=beta`，closed beta 使用 prod 模式配置；第一阶段采用受控 API key 身份、人工真实 CSV、外部购买记录、购买证据等级、单机 Compose + COS + HTTPS 反代、文本导购和识图优先。
- 已完成阶段 1 发布底座：新增 prod Compose、readiness token 和深探针、closed beta smoke/verify 脚本、外部购买立即可评价策略、`orders:advance` 独立 scope、`.env.prod.example` 和 closed beta runbook。
- 已完成普通用户手机号 OTP 登录、refresh/logout/me、用户 JWT scope 兼容和 Android auth token store/repository 接入；真实短信 provider 仍不在当前版本范围内。
- 已完成组合方案推荐：`bundle_recommend` 意图、`bundle_plans` 契约、方案生成服务、JSON/SSE chat 返回、Android 方案卡片和 demo bundle 流程测试。
- 已完成能力补齐：场景需求结构化已扩展到日期、地点、时长、场合、风格、必选和排除品类；购物车、地址和 shadow checkout 已覆盖后端 API、对话动作和 Android 购物车页；拍照找货已走视觉特征提取、混合相似检索和 Android 相似商品展示。
- 已完成后台作业 artifact：商品导入、索引构建、COS 图片迁移、MySQL 备份检查和 release prepare 聚合 artifact 已纳入发布记录要求。
- 2026-06-07 常规维护基线：工作区干净；`python scripts/validate_docs.py`、`python scripts/validate_entropy.py`、`.\\.venv\\Scripts\\python.exe -m pytest` 和 `auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild` 均通过。

## 验证

- `python scripts/validate_docs.py`
- `python scripts/validate_providers.py`
- `python scripts/validate_repo_lint.py`
- `python scripts/validate_entropy.py`
- `.\\.venv\\Scripts\\python.exe -m pytest`
- `cd android-app; .\gradlew.bat :app:assembleDebug`
- `cd admin-web; npm run build`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild -SkipAdminWebBuild`
