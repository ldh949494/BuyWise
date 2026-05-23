# 当前计划

## 目标

实现 P1 订单反馈闭环：在不建设真实交易平台的前提下，补齐模拟下单、付款/物流状态、收货后评价提示和已购反馈加权分析，让 BuyWise 的推荐与商品分析形成购买后反馈闭环。

## 活跃任务

- [ ] 按 `docs/design/p1-order-feedback-loop.md` 实现后端交易影子模型和反馈闭环。
- [ ] 新增 Alembic 迁移：创建 `orders`、`order_items`，扩展 `reviews`，补齐必要索引。
- [ ] 新增订单、待评价提示、已购评价提交/更新/撤回 API，并注册到 `app/api/router.py`。
- [ ] 扩展 repository 和 service：订单创建、状态推进、待评价查询、提示忽略、已购反馈归属校验、评价权重计算和商品反馈聚合。
- [ ] 将已购反馈信号接入推荐、对比、商品详情和聊天分析，但保持预算、品类、库存、场景等主约束优先。
- [ ] 更新 Android 最小闭环：商品详情记录购买、待评价提示、评价表单和反馈摘要。
- [ ] 更新 `docs/reference/api.md`、`docs/reference/configuration.md`、Android 边界和演示检查清单。
- [ ] 后端、Android、运行时或可观测边界变化时，更新架构文档。
- [ ] 公共端点、环境变量或脚本变化时，更新参考文档。
- [ ] 修改文档后运行 `python scripts/validate_docs.py`。
- [ ] 重大结构变化后运行 `python scripts/doc_gardening.py`。
- [ ] 演示前按 `docs/plans/demo-checklist.md` 逐项确认 Android 主路径和 Swagger 备用路径。

## 验证

- `python scripts/validate_docs.py`
- `python scripts/validate_providers.py`
- `python scripts/validate_repo_lint.py`
- `python scripts/validate_entropy.py`
- `.\\.venv\\Scripts\\python.exe -m pytest`
- `flutter analyze`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`
