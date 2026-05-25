# 设计：Closed Beta 后端并发保护

Status: Implemented

## 背景

Closed beta 阶段预计为单机 Compose 部署，峰值按 10-20 个真实用户、3-5 个同时 AI 对话、1-2 个同时识图或语音请求设计。当前高风险路径是 `/api/v1/ai/chat`、`/api/v1/ai/chat/stream`、`/api/v1/vision`、`/api/v1/speech` 和 `/api/v1/upload`，其中聊天、识图和语音会在请求路径内调用外部 AI provider。

本阶段目标是保护单进程后端和外部 provider，不引入 Redis、任务队列或真实排队系统。

## 方案

- 使用进程内限流保护入口请求。限流身份优先使用 Bearer token 解析出的 API key subject；没有有效 principal 时使用客户端 IP。
- 不同端点独立分桶：聊天、识图、语音和上传互不抢占额度。
- 频率超限返回 `429 rate_limited`，并携带 `Retry-After`、`limit_scope`、`retry_after_seconds` 和 `request_id`。
- 使用进程内容量闸门保护外部 AI provider：`llm`、`vision` 和 `speech` 分别配置最大并发。
- 容量不足返回 `503 capacity_limited`，provider 超时返回 `504 provider_timeout`。
- 文本聊天在 LLM 容量不足时不排队：后端保留 RAG/规则排序结果，返回商品卡片和模板化说明，并在 `extra` 中标记 `degraded=true`、`degraded_reason=llm_capacity_limited`。
- 流式聊天先发送商品结果；如果 LLM 容量不足，发送 `fallback` 事件和 degraded `done` 事件。
- 识图和语音是输入理解步骤，不做同等模板降级；容量不足或超时时快速失败，客户端提示用户改用文字输入。

配置项：

- `AI_LLM_MAX_CONCURRENCY`
- `AI_VISION_MAX_CONCURRENCY`
- `AI_SPEECH_MAX_CONCURRENCY`
- `AI_PROVIDER_TIMEOUT_SECONDS`
- `CAPACITY_RETRY_AFTER_SECONDS`
- `CHAT_RATE_LIMIT_PER_MINUTE`
- `VISION_RATE_LIMIT_PER_MINUTE`
- `SPEECH_RATE_LIMIT_PER_MINUTE`
- `UPLOAD_RATE_LIMIT_PER_MINUTE`

## 影响

- `app/core/traffic.py` 提供进程内限流、容量闸门和 provider timeout helper。
- `app/core/providers.py` 在通用 request middleware 中执行限流。
- `app/ai/llm_client.py`、`app/integrations/vision_client.py` 和 `app/integrations/speech_client.py` 在外部 provider 调用前执行容量保护和 timeout。
- `app/services/chat_service.py` 和 `app/services/chat_stream_service.py` 实现 LLM 容量不足时的聊天降级。
- `.env.example` 和 `.env.prod.example` 暴露 closed beta 可调参数。

进程内方案只适用于当前单 Uvicorn worker 部署。后续开启多 worker 或多后端实例时，需要迁移到 Redis 等共享限流与容量控制。

## 验证

- `tests/test_traffic_controls.py` 覆盖聊天限流返回 429，以及 LLM 容量不足时非流式聊天降级。
- `tests/test_demo_showcase_flow.py` 验证主聊天推荐路径未被破坏。
- `tests/test_intent_service.py` 验证 LLM 意图抽取失败时仍回退规则抽取。

## 最近检查

2026-05-25
