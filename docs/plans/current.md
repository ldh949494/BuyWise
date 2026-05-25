# 当前计划

## 目标

实现 P1 订单反馈闭环：在不建设真实交易平台的前提下，补齐模拟下单、付款/物流状态、收货后评价提示和已购反馈加权分析，让 BuyWise 的推荐与商品分析形成购买后反馈闭环。

## 活跃任务

- [ ] 补齐 Android 订单反馈闭环的剩余体验：完整评价表单、可选标签/场景输入、反馈摘要展示和必要的错误状态。
- [ ] 更新 Android 边界和演示检查清单，明确订单反馈、固定资源多模态联调和当前 Android 演示限制。
- [ ] 后端、Android、运行时或可观测边界继续变化时，更新架构文档。
- [ ] 公共端点、环境变量或脚本继续变化时，更新参考文档。
- [ ] 修改文档后运行 `python scripts/validate_docs.py`。
- [ ] 重大结构变化后运行 `python scripts/doc_gardening.py`。
- [ ] 演示前按 `docs/plans/demo-checklist.md` 逐项确认 Android 主路径和 Swagger 备用路径。

## 已完成记录

- 后端已按 `docs/design/p1-order-feedback-loop.md` 实现交易影子模型和反馈闭环：`orders`、`order_items`、扩展 `reviews`、订单状态推进、待评价提示、已购评价提交/更新/撤回、归属校验和反馈权重聚合。
- 已购反馈信号已接入推荐、对比、商品详情和聊天分析，并保持预算、品类、库存、场景等主约束优先。
- 商品维护、RAG 演示质量、多模态 provider、上传清理、release prepare、脚本参考和主要 API/config 参考已同步到实现。
- P1 认证边界保持轻量：订单、反馈和已购评价保留可选 Bearer token，真实生产用户体系后续迁移。
- 后台维护策略保持脚本加外部调度，不在 FastAPI 进程内引入常驻 scheduler。
- Android 已有部分闭环：商品详情记录购买、首页待评价提示和一键提交固定内容评价。

## 验证

- `python scripts/validate_docs.py`
- `python scripts/validate_providers.py`
- `python scripts/validate_repo_lint.py`
- `python scripts/validate_entropy.py`
- `.\\.venv\\Scripts\\python.exe -m pytest`
- `flutter analyze`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`
