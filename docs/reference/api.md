# API 参考说明

后端默认把公共路由注册在 `/api/v1` 下。

## 路由分组

- 健康检查：`/api/v1/health`
- 商品：`/api/v1/products`
- 商品对比：`/api/v1/products/compare`
- AI 聊天：`/api/v1/ai/chat`
- AI 聊天流式接口：`/api/v1/ai/chat/stream`
- RAG 搜索：`/api/v1/rag/search`
- 上传：`/api/v1/upload`
- 视觉识别：`/api/v1/vision/recognize`
- 语音识别：`/api/v1/speech/asr`

## 生成式参考

运行后端并打开 `/docs` 可查看 OpenAPI UI。浏览器验证脚本 `scripts/browser_check.py` 可以捕获文档页面。

## 响应说明

- 商品响应包含可选扩展电商字段：`sku`、`product_url`、`image_urls`、`stock_status`、`review_summary` 和 `price_history`。
- 聊天响应通过 `extra.session_id` 返回持久化会话标识。
- 聊天流式响应使用 Server-Sent Events，事件包括 `meta`、`status`、`token`、`products`、`done` 和 `error`。
- 聊天商品卡片包含解释字段：`budget_match`、`scenario_match`、`conflicts` 和 `alternatives`。

## 鉴权说明

- `POST /api/v1/upload` 需要 `Authorization: Bearer <token>`，并具备 `upload:write` scope。
- `POST /api/v1/products` 需要 `Authorization: Bearer <token>`，并具备 `products:write` scope。
- 当前 Android 集成流程中，商品浏览、详情、对比和 AI 聊天保持公开访问。
- 认证、请求上下文、错误、遥测和日志必须通过 `app.core.providers` 访问；`scripts/validate_providers.py` 会阻止直接导入 provider 实现模块。

| 流程 | 方法 | 路径 | 身份 | 所需 scope |
| --- | --- | --- | --- | --- |
| 健康检查 | `GET` | `/api/v1/health` | 公开 | 无 |
| 商品浏览 | `GET` | `/api/v1/products` | 公开 | 无 |
| 商品详情 | `GET` | `/api/v1/products/{product_id}` | 公开 | 无 |
| 商品创建 | `POST` | `/api/v1/products` | Bearer token | `products:write` |
| 商品对比 | `POST` | `/api/v1/products/compare` | 公开 | 无 |
| AI 导购 | `POST` | `/api/v1/ai/chat` | 公开 | 无 |
| AI 导购流式接口 | `POST` | `/api/v1/ai/chat/stream` | 公开 | 无 |
| RAG 搜索 | `POST` | `/api/v1/rag/search` | 公开 | 无 |
| 上传 | `POST` | `/api/v1/upload` | Bearer token | `upload:write` |
| 视觉识别 | `POST` | `/api/v1/vision/recognize` | 公开 | 无 |
| 语音识别 | `POST` | `/api/v1/speech/asr` | 公开 | 无 |

## Android 合同流

原生 Android 客户端优先依赖以下后端流程：

- 商品浏览：`GET /api/v1/products` 支持类目、关键词、价格和分页筛选；`GET /api/v1/products/{product_id}` 获取详情。
- 商品对比：`POST /api/v1/products/compare`，请求体包含 `product_ids` 和可选 `user_need`。
- AI 导购：`POST /api/v1/ai/chat` 返回 JSON，或 `POST /api/v1/ai/chat/stream` 返回 SSE token 流；请求包含 `session_id` 和 `message`，可选 `image_url` 和 `audio_url`。

`app.scripts.seed_products.seed_android_contract_products` 提供这些流程使用的确定性商品数据。`tests/test_android_contract_api.py` 锁定 Android 使用的响应形状，后续真实 AI provider 可以调整排序和文案，但不能移除必需字段。

## Android 本地联调

Android 应用使用 `BuildConfig.BUYWISE_API_BASE_URL`，默认值是 `http://10.0.2.2:8000`，用于模拟器访问宿主机后端。

本地联调步骤：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_database
.\.venv\Scripts\python.exe -m app.scripts.seed_products
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

然后从 `android-app/` 构建或运行 Android 应用。应用应能在启动时加载商品、自动对比可用商品、从后端刷新商品详情，并通过 `/api/v1/ai/chat/stream` 流式展示 AI 导购回复。

后端不可用时，本次集成不自动回退到 mock 数据；UI 应展示错误和重试入口。识图、上传和语音仍是本地演示，不属于当前 Android 集成范围。

## Swagger 备用演示

Android 作为主演示路径，Swagger 和 API 请求作为现场兜底路径。准备步骤：

完整顺序见 `docs/plans/demo-checklist.md`。

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_database
.\.venv\Scripts\python.exe -m app.scripts.seed_products --profile demo
.\.venv\Scripts\python.exe -m app.scripts.build_vector_index
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

打开 `http://127.0.0.1:8000/docs`，按顺序展示：

- `GET /api/v1/health`
- `GET /api/v1/products?page=1&page_size=5`
- `POST /api/v1/products/compare`
- `POST /api/v1/ai/chat`

推荐聊天请求体：

```json
{
  "session_id": "demo-swagger-session",
  "message": "帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高"
}
```

也可以直接运行 API 备用检查：

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_api_check.py --base-url http://127.0.0.1:8000
```

## RAG 质量闭环

RAG 检索质量通过 `data/rag_eval/` 下的 profile 评测集跟踪。运行 `python -m app.scripts.evaluate_rag --profile android-contract` 可验证 Android 合同商品，运行 `python -m app.scripts.evaluate_rag --profile demo` 可验证演示商品；报告包含 `recall@k`、`top1_accuracy`、`mrr@k` 和当前失败案例。`tests/test_rag_eval.py` 对固定评测集提供轻量回归门禁。运行 `python -m app.scripts.check_vector_index --profile demo` 可检查演示索引缺失或陈旧商品 ID。
