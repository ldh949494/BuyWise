# 设计：P1 AI 导购与 RAG 演示质量

Status: Implemented

## 背景

BuyWise 当前优先保证演示链路稳定，同时保留后续扩展到真实质量闭环的空间。导购质量和 RAG 质量需要覆盖固定 demo 商品、常见中文表达、可解释推荐和索引一致性诊断，但不在 P1 内追求所有线上长尾问题。

## 方案

P1 以演示稳定性为第一目标。真实 LLM 输出样例回归测试锁定结构化 need 和商品卡片，不锁最终自然语言 reply 全文。推荐排序中的 score 仅作为内部排序细节，稳定合同是排序顺序、匹配布尔值、冲突和推荐理由关键片段。

RAG eval 按 seed profile 分层：`android-contract` 绑定 Android 合同商品 `1001-1005`，`demo` 绑定演示商品 `1101-1105`。无结果 fallback 固定为三段式：先放宽预算，再放宽偏好或场景，最后才推荐相邻品类。RAG 调试信息先进入结构化日志和 eval report，不进入公开 API 响应。

索引健康检查第一阶段以服务函数和脚本输出实现，报告 collection count、DB 商品数量、索引缺失 ID 和陈旧 ID。公开健康 API 后置。

## 影响

- `app/services/intent_llm.py`：扩充 LLM 输出归一化回归样例。
- `app/services/recommend_service.py`：拆分预算、场景、偏好、库存、口碑评分。
- `app/ai/rag_pipeline.py`：增加 fallback 阶段和过滤原因结构化日志。
- `app/scripts/evaluate_rag.py`：支持 `--profile android-contract|demo`。
- `app/services/product_index_service.py`：提供索引健康检查服务函数。
- `data/rag_eval/`：分离 Android contract 与 demo eval 数据。

## 验证

- 意图回归测试断言真实 LLM JSON 样例的结构化 need。
- 推荐排序测试断言相对顺序、匹配布尔值、冲突和理由片段。
- RAG eval 测试分别验证 Android contract 和 demo profile。
- 索引健康测试覆盖 missing 与 stale product id。
- 修改文档后运行 `python scripts/validate_docs.py`。

## 剩余边界/后续工作

- 公开索引健康 API 仍后置；当前健康检查通过服务函数和 `app.scripts.check_vector_index` 暴露。
- RAG 调试信息仍只进入结构化日志和评测报告，不进入公开 API 响应。
- P1 只锁定演示质量和固定 profile 回归，不承诺覆盖真实线上长尾 query。

## 最近检查

2026-05-25
