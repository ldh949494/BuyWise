# 当前计划

## 目标

按 `docs/design/closed-beta-real-engineering.md` 将 BuyWise 从演示闭环推进到 closed beta 真实工程落地：使用 prod 模式配置、受控用户 token、真实商品 CSV、外部购买记录、购买证据等级、Android beta 体验、单机 Compose 部署和最低可恢复运维能力。

## 活跃任务

- [x] 身份与权限：订单、待评价和评价接口在 prod 模式强制 Bearer token，引入 `orders:*` 和 `feedback:*` scope，Android repository 统一 Authorization 注入并支持 `BUYWISE_BETA_TOKEN`。
- [x] 购买证据语义：将 closed beta 外部购买记录从 `verified_purchase` 语义调整为 `purchase_evidence` 或等价 evidence level，推荐和对比权重按 evidence level 计算。
- [x] 真实商品目录：定义 beta catalog CSV 规则，要求真实商品链接和图片，固定发布流程为 import CSV、rebuild index 和 check index，禁止与 demo seed 混用。
- [ ] Android beta 体验：记录外部购买表单、完整反馈表单、待评价错误状态、反馈摘要展示和缺 token 禁用状态。
- [ ] 部署与运维：补充 prod-mode closed beta env、单机 Compose、COS、HTTPS 反代、readiness、MySQL 备份恢复、Chroma rebuild 和回滚 runbook。
- [ ] AI provider 策略：closed beta 默认真实化文本导购和识图，语音保持可选实验能力，并补充失败兜底和第三方处理说明。
- [ ] 公共端点、环境变量、脚本、Android 行为或部署流程变化时，同步参考文档和架构文档。
- [ ] 修改文档后运行 `python scripts/validate_docs.py`。
- [ ] 重大结构变化后运行 `python scripts/doc_gardening.py`。
- [ ] closed beta 发布前运行后端、Android、数据导入、索引健康、readiness 和 smoke 验证。

## 已完成记录

- 后端已按 `docs/design/p1-order-feedback-loop.md` 实现交易影子模型和反馈闭环：`orders`、`order_items`、扩展 `reviews`、订单状态推进、待评价提示、已购评价提交/更新/撤回、归属校验和反馈权重聚合。
- 已购反馈信号已接入推荐、对比、商品详情和聊天分析，并保持预算、品类、库存、场景等主约束优先。
- 商品维护、RAG 演示质量、多模态 provider、上传清理、release prepare、脚本参考和主要 API/config 参考已同步到实现。
- P1 认证边界保持轻量：订单、反馈和已购评价保留可选 Bearer token，真实生产用户体系后续迁移。
- 后台维护策略保持脚本加外部调度，不在 FastAPI 进程内引入常驻 scheduler。
- Android 已有部分闭环：商品详情记录购买、首页待评价提示和一键提交固定内容评价。
- 已完成 closed beta 方向决策：不新增 `APP_ENV=beta`，closed beta 使用 prod 模式配置；第一阶段采用受控 API key 身份、人工真实 CSV、外部购买记录、购买证据等级、单机 Compose + COS + HTTPS 反代、文本导购和识图优先。

## 验证

- `python scripts/validate_docs.py`
- `python scripts/validate_providers.py`
- `python scripts/validate_repo_lint.py`
- `python scripts/validate_entropy.py`
- `.\\.venv\\Scripts\\python.exe -m pytest`
- `flutter analyze`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`
