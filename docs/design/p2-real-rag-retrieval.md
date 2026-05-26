# 设计：P2 真实 RAG 召回

Status: Implemented

## 背景

阶段 2 的目标是把演示 RAG 推进到可评估的真实召回链路：真实 embedding provider、固定索引重建流程、真实 beta 商品评测、二阶段 rerank 和失败可诊断。

## 方案

Embedding 独立 provider 化，保留稳定 mock，并增加 OpenAI-compatible embeddings API。`EMBEDDING_BASE_URL` 和 `EMBEDDING_API_KEY` 为空时回退到 LLM 配置；prod 模式默认不允许 `EMBEDDING_PROVIDER=mock`。

Closed beta 真实 CSV 导入仍由 `import_products` 只负责数据库写入。发布入口 `release_prepare.ps1 -ImportCsv <path> -RequireRealCatalog` 强制同时执行 `-BuildIndex -IndexMode rebuild -CheckIndex`，避免真实目录导入后索引不一致。

RAG eval 增加 `beta-fixture` profile，使用 repo 内小规模真实商品 fixture 和场景化 query；`--retrieval vector` 会在临时 Chroma 目录重建索引并执行召回评估。`beta-live` 暂不进入自动测试，作为后续发布环境验证入口。

向量召回后先做 RAG 硬过滤和 fallback，再复用 `RecommendService` 做二阶段 rerank，统一库存、预算、场景、偏好、评分、评论和购买反馈信号。

Diagnostics 进入结构化日志和 eval report，不进入公开 RAG API 响应。字段至少包括 `source`、`fallback_stage`、`filter_reasons`、`retrieved_ids`、`final_ids` 和 `latency_ms`。

## 验证

- Embedding provider 单测覆盖 mock 稳定性和 OpenAI-compatible embeddings API 调用。
- Release prepare 测试覆盖真实目录导入必须 rebuild 和 check。
- RAG eval 测试覆盖 `beta-fixture` 数据完整性和 vector retrieval diagnostics。
- RAG pipeline 测试覆盖向量候选、过滤和最终 diagnostics。
