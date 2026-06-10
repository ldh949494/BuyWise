# API 参考说明

后端默认把公共路由注册在 `/api/v1` 下。

## 路由分组

- 健康检查：`/api/v1/health`、`/api/v1/ready`
- 商品：`/api/v1/products`
- 商品对比：`/api/v1/products/compare`
- 购物车与默认地址：`/api/v1/cart`、`/api/v1/addresses`
- 影子订单：`/api/v1/orders`
- 待评价提示：`/api/v1/feedback/prompts`
- 已购评价：`/api/v1/reviews`
- AI 聊天：`/api/v1/ai/chat`
- AI 聊天流式接口：`/api/v1/ai/chat/stream`
- AI 导购慢接口：`/api/v1/ai/guide/stream`
- AI 导购追问快接口：`/api/v1/ai/guide/follow-up/stream`
- AI 对比追问接口：`/api/v1/ai/compare/follow-up/stream`
- 导购偏好：`/api/v1/guide/preferences`
- RAG 搜索：`/api/v1/rag/search`
- 上传：`/api/v1/upload`
- 视觉识别：`/api/v1/vision/recognize`
- 拍照找货：`/api/v1/visual-search`
- 语音识别：`/api/v1/speech/asr`
- 普通用户认证：`/api/v1/auth/...`
- 内部后台：`/api/v1/admin/...`

## 生成式参考

运行后端并打开 `/docs` 可查看 OpenAPI UI。浏览器验证脚本 `scripts/browser_check.py` 可以捕获文档页面。

## 响应说明

- 商品响应包含可选扩展电商字段：`sku`、`product_url`、`image_urls`、`stock_status`、`review_summary`、`feedback_metrics` 和 `price_history`。
- 购物车、地址和 checkout 是 BuyWise 内部交易影子模型：支持会话商品加入、数量编辑、删除、默认地址结算和订单快照，不代表真实支付或真实履约。
- 订单响应表达模拟付款、物流状态和订单项快照；购物车 checkout 创建的订单会带 `payment_mode=shadow_paid`、`address_snapshot`、`cart_snapshot` 和 `checkout_session_id`。
- 已购评价通过服务端校验订单项归属和已收货状态后写入 `reviews`。Closed beta 外部购买记录使用 `purchase_evidence=buywise_recorded`，不声明平台验真；未来接入平台验真后才使用 `platform_verified` 等级。
- 订单相关接口只表示 BuyWise 内部的购买记录和影子订单状态；`POST /api/v1/orders/{order_id}/advance` 仅用于 demo、smoke 或管理推进。
- 聊天响应通过 `extra.session_id` 返回持久化会话标识。
- 聊天流式响应使用 Server-Sent Events，事件包括 `meta`、`status`、`token`、`products`、`heartbeat`、`done` 和 `error`。
- 流式聊天不长期暴露 `fallback` 事件；降级通过 `status.stage=fallback` 和 `done.degraded=true` 表达。
- 聊天商品卡片包含解释字段：`budget_match`、`scenario_match`、`conflicts` 和 `alternatives`。
- AI 导购会在组合场景中返回 `bundle_plans`；结构化需求包含日期、地点、时长、场合、风格偏好、必选品类和排除品类，用于跨类目检索和方案编排。
- AI 导购追问支持会话内购物车动作，如“把刚才那款加到购物车”“删掉第二个”“下单吧，地址用默认的”；动作结果会作为普通回复或 SSE token/done 返回。
- AI 对比追问基于客户端传入的当前对比商品、摘要和 winner 回答，不依赖导购 `session_id` 或推荐快照。
- 拍照找货接口返回 `recognized` 视觉特征、相似商品 `products` 和 `fallback_used`，视觉索引为空时会退回文本/RAG 候选。
- RAG 搜索响应的 `items` 使用强类型 `RagItem`，只承诺 `product_id`、`name`、`price`、`score`、`reason`、`category`、`platform`、`product_url` 和 `stock_status`。

## 鉴权说明

- `POST /api/v1/upload` 需要 `Authorization: Bearer <token>`，并具备 `upload:write` scope。
- `POST`、`PATCH` 和 `DELETE /api/v1/products...` 需要 `Authorization: Bearer <token>`，并具备 `products:write` scope。
- `/api/v1/auth/otp/request` 和 `/api/v1/auth/otp/verify` 使用手机号验证码登录；dev/test mock OTP 会返回 `debug_otp`，prod 不返回验证码。
- 普通用户登录后使用 user access JWT 调用订单、评价和上传接口；用户 JWT 固定具备 `orders:read`、`orders:write`、`feedback:read`、`feedback:write` 和 `upload:write`，不具备 `products:write` 或后台权限。
- `APP_ENV=prod` 时，订单、待评价提示和已购评价接口必须携带 `Authorization: Bearer <token>`；dev/test 仍允许无 token 使用 `DEMO_USER_REF` 演示身份。
- `APP_ENV=prod` 时，`/api/v1/ready` 必须携带 `READINESS_TOKEN`，可通过 `Authorization: Bearer <token>` 或 `X-Readiness-Token` 传入。
- `/api/v1/admin/...` 使用管理员账号登录后签发的 JWT access token，不复用 `AUTH_API_KEYS` scope。
- 当前 Android 集成流程中，商品浏览、详情、对比和 AI 聊天保持公开访问。
- 认证、请求上下文、错误、遥测和日志必须通过 `app.core.providers` 访问；`scripts/validate_providers.py` 会阻止直接导入 provider 实现模块。

| 流程 | 方法 | 路径 | 身份 | 所需 scope |
| --- | --- | --- | --- | --- |
| 健康检查 | `GET` | `/api/v1/health` | 公开 | 无 |
| Readiness | `GET` | `/api/v1/ready` | prod readiness token；dev/test 公开 | 无 |
| 商品浏览 | `GET` | `/api/v1/products` | 公开 | 无 |
| 商品详情 | `GET` | `/api/v1/products/{product_id}` | 公开 | 无 |
| 商品创建 | `POST` | `/api/v1/products` | Bearer token | `products:write` |
| 商品更新 | `PATCH` | `/api/v1/products/{product_id}` | Bearer token | `products:write` |
| 商品下架 | `DELETE` | `/api/v1/products/{product_id}` | Bearer token | `products:write` |
| 请求登录验证码 | `POST` | `/api/v1/auth/otp/request` | 公开 | 无 |
| 校验验证码登录 | `POST` | `/api/v1/auth/otp/verify` | 公开 | 无 |
| 刷新用户 token | `POST` | `/api/v1/auth/refresh` | refresh token | 无 |
| 用户退出登录 | `POST` | `/api/v1/auth/logout` | refresh token | 无 |
| 当前用户资料 | `GET` | `/api/v1/auth/me` | User JWT | 无 |
| 管理员登录 | `POST` | `/api/v1/admin/auth/login` | 公开 | 无 |
| 后台商品列表 | `GET` | `/api/v1/admin/products` | Admin JWT | 无 |
| 后台商品详情 | `GET` | `/api/v1/admin/products/{product_id}` | Admin JWT | 无 |
| 后台商品创建 | `POST` | `/api/v1/admin/products` | Admin JWT | 无 |
| 后台商品更新 | `PATCH` | `/api/v1/admin/products/{product_id}` | Admin JWT | 无 |
| 后台商品下架 | `DELETE` | `/api/v1/admin/products/{product_id}` | Admin JWT | 无 |
| 后台上传 | `POST` | `/api/v1/admin/upload` | Admin JWT | 无 |
| 商品对比 | `POST` | `/api/v1/products/compare` | 公开 | 无 |
| 购物车读取 | `GET` | `/api/v1/cart` | prod Bearer token；dev/test 可选 | `orders:read` |
| 加入购物车 | `POST` | `/api/v1/cart/items` | prod Bearer token；dev/test 可选 | `orders:write` |
| 修改购物车数量 | `PATCH` | `/api/v1/cart/items/{item_id}` | prod Bearer token；dev/test 可选 | `orders:write` |
| 删除购物车商品 | `DELETE` | `/api/v1/cart/items/{item_id}` | prod Bearer token；dev/test 可选 | `orders:write` |
| 购物车结算 | `POST` | `/api/v1/cart/checkout` | prod Bearer token；dev/test 可选 | `orders:write` |
| 地址列表 | `GET` | `/api/v1/addresses` | prod Bearer token；dev/test 可选 | `orders:read` |
| 创建地址 | `POST` | `/api/v1/addresses` | prod Bearer token；dev/test 可选 | `orders:write` |
| 设置默认地址 | `PATCH` | `/api/v1/addresses/{address_id}/default` | prod Bearer token；dev/test 可选 | `orders:write` |
| 创建模拟订单 | `POST` | `/api/v1/orders` | prod Bearer token；dev/test 可选 | `orders:write` |
| 订单列表 | `GET` | `/api/v1/orders` | prod Bearer token；dev/test 可选 | `orders:read` |
| 订单详情 | `GET` | `/api/v1/orders/{order_id}` | prod Bearer token；dev/test 可选 | `orders:read` |
| 推进模拟物流 | `POST` | `/api/v1/orders/{order_id}/advance` | prod Bearer token；dev/test 可选 | `orders:advance` |
| 待评价提示 | `GET` | `/api/v1/feedback/prompts` | prod Bearer token；dev/test 可选 | `feedback:read` |
| 忽略待评价提示 | `POST` | `/api/v1/feedback/prompts/{order_item_id}/dismiss` | prod Bearer token；dev/test 可选 | `feedback:write` |
| 提交已购评价 | `POST` | `/api/v1/reviews/from-order-item` | prod Bearer token；dev/test 可选 | `feedback:write` |
| 更新已购评价 | `PUT` | `/api/v1/reviews/{review_id}` | prod Bearer token；dev/test 可选 | `feedback:write` |
| 撤回已购评价 | `POST` | `/api/v1/reviews/{review_id}/withdraw` | prod Bearer token；dev/test 可选 | `feedback:write` |
| AI 导购 | `POST` | `/api/v1/ai/chat` | 公开 | 无 |
| AI 导购流式接口 | `POST` | `/api/v1/ai/chat/stream` | 公开 | 无 |
| AI 导购慢接口 | `POST` | `/api/v1/ai/guide/stream` | 公开 | 无 |
| AI 导购追问快接口 | `POST` | `/api/v1/ai/guide/follow-up/stream` | 公开 | 无 |
| AI 对比追问接口 | `POST` | `/api/v1/ai/compare/follow-up/stream` | 公开 | 无 |
| 导购偏好读取 | `GET` | `/api/v1/guide/preferences` | User JWT | 无 |
| 导购偏好保存 | `PUT` | `/api/v1/guide/preferences` | User JWT | 无 |
| 导购偏好清除 | `DELETE` | `/api/v1/guide/preferences` | User JWT | 无 |
| RAG 搜索 | `POST` | `/api/v1/rag/search` | 公开 | 无 |
| 上传 | `POST` | `/api/v1/upload` | Bearer token | `upload:write` |
| 视觉识别 | `POST` | `/api/v1/vision/recognize` | 公开 | 无 |
| 拍照找货 | `POST` | `/api/v1/visual-search` | 公开 | 无 |
| 语音识别 | `POST` | `/api/v1/speech/asr` | 公开 | 无 |

## Android 合同流

原生 Android 客户端优先依赖以下后端流程：

- 商品浏览：`GET /api/v1/products` 支持类目、关键词、价格和分页筛选；`GET /api/v1/products/{product_id}` 获取详情。
- 商品维护：`POST /api/v1/products` 创建商品，`PATCH /api/v1/products/{product_id}` 更新商品，`DELETE /api/v1/products/{product_id}` 软下架商品。下架商品默认不进入公开浏览、详情、RAG、推荐和对比。
- 商品对比：`POST /api/v1/products/compare`，请求体包含 `product_ids` 和可选 `user_need`。对比页继续追问使用 `POST /api/v1/ai/compare/follow-up/stream`，请求携带当前对比 `items`、`summary`、`winner_id` 和用户问题，不要求先完成 AI 导购。
- 购物车与下单：`GET /api/v1/cart` 读取当前 active cart，`POST /api/v1/cart/items` 加入商品，`PATCH /api/v1/cart/items/{item_id}` 修改数量，`DELETE /api/v1/cart/items/{item_id}` 删除商品；`GET/POST/PATCH /api/v1/addresses` 管理默认地址；`POST /api/v1/cart/checkout` 用默认地址生成 BuyWise 影子订单并清空购物车。
- 订单反馈闭环：`POST /api/v1/orders` 仍支持直接记录购买；购物车 checkout 会生成同一订单模型。closed beta 外部购买记录带 `external_platform` 后可直接进入待评价；`POST /api/v1/orders/{order_id}/advance` 仅用于 demo、smoke 或管理推进；`GET /api/v1/feedback/prompts` 获取待评价项，`POST /api/v1/reviews/from-order-item` 提交已购评价。
- AI 导购：`POST /api/v1/ai/chat` 返回 JSON，`POST /api/v1/ai/chat/stream` 保留为兼容流式入口。Android 主链路使用快慢接口：`POST /api/v1/ai/guide/stream` 用于开始或刷新导购，完整执行理解、检索、排序和生成；`POST /api/v1/ai/guide/follow-up/stream` 用于基于当前 `session_id` 的最新推荐快照继续追问，不重新检索和排序。请求包含 `session_id` 和 `message`，可选 `image_url`、`audio_url`、`ignore_saved_preferences` 和 `temporary_preferences`。普通用户带 User JWT 时会自动合并账号级导购偏好；单品需求返回 `products`，组合搭配需求返回 `bundle_plans`，响应会返回结构化 `applied_preferences`。
- 导购偏好：`GET /api/v1/guide/preferences` 获取账号级导购偏好，`PUT /api/v1/guide/preferences` 保存结构化偏好，`DELETE /api/v1/guide/preferences` 清除偏好。偏好包括预算策略、单品/整套预算区间、核心偏好、排除项、已有设备和推荐呈现方式。
- 拍照找货：Android 上传图片后调用 `POST /api/v1/visual-search`，将识别出的品类、颜色、材质、版型、风格和品牌线索转成相似商品候选。返回候选可继续进入详情、对比或加入购物车。

### AI 导购 SSE 事件契约

`POST /api/v1/ai/chat/stream`、`POST /api/v1/ai/guide/stream`、`POST /api/v1/ai/guide/follow-up/stream` 和 `POST /api/v1/ai/compare/follow-up/stream` 返回 `text/event-stream`。事件类型固定为：

| 事件 | payload |
| --- | --- |
| `meta` | `{"session_id": "..."}` |
| `status` | `{"stage": "intent|retrieval|generation|fallback", "message": "..."}` |
| `token` | `{"text": "..."}` |
| `products` | `{"need_clarify": false, "structured_need": StructuredNeed, "items": ProductCard[], "bundle_plans": BundlePlan[], "applied_preferences": AppliedPreferences}` |
| `heartbeat` | `{"status": "ok"}` |
| `done` | `{"reply": "...", "degraded": false, "degraded_reason": null, "should_refresh": false, "refresh_reason": null}` |
| `error` | `{"code": "chat_stream_failed|chat_stream_timeout", "message": "...", "session_id": "..."}` |

`heartbeat` 用于连接空闲期间保持 SSE 长连接活跃。`error` 只用于流已经开始后无法改 HTTP 状态的异常兜底或总时长超时；空结果和容量降级都不使用 `error`：空结果通过 `products.items=[]` 和 `done.reply` 表达，容量降级通过 `status.stage=fallback` 和 `done.degraded=true` 表达。导购已经发送 `products` 后如果最终总结超时，会返回 `done.degraded=true` 和 `degraded_reason=stream_generation_timeout`，客户端应保留已展示的商品结果。`done.reply` 始终包含最终完整回复，供客户端补偿 token 拼接或处理无 token 的降级路径。

追问快接口不会自动升级到完整导购。如果缺少 `session_id`、找不到当前会话的推荐快照，或用户问题明显改变推荐条件，`done.should_refresh=true`，`refresh_reason` 说明原因，客户端应引导用户刷新导购或调用 `/api/v1/ai/guide/stream`。

`app.scripts.seed_products.seed_android_contract_products` 提供这些流程使用的确定性商品数据。`tests/test_android_contract_api.py` 锁定 Android 使用的响应形状，后续真实 AI provider 可以调整排序和文案，但不能移除必需字段。

## Android 本地联调

Android 应用使用 `BuildConfig.BUYWISE_API_BASE_URL`，默认值是 `http://10.0.2.2:8000`，用于模拟器访问宿主机后端。

Closed beta 构建使用 `BUYWISE_BETA_TOKEN` 注入受控用户 token。订单、待评价、评价和上传联调请求会带上该 token；未配置时，Android 会禁用或报错提示需要 beta token 的用户能力。

本地联调步骤：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_database
.\.venv\Scripts\python.exe -m app.scripts.seed_products
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

然后从 `android-app/` 构建或运行 Android 应用。应用应能在启动时加载商品、自动对比可用商品、从后端刷新商品详情，并通过 `/api/v1/ai/guide/stream` 开始导购、通过 `/api/v1/ai/guide/follow-up/stream` 流式展示导购追问、通过 `/api/v1/ai/compare/follow-up/stream` 流式展示对比追问回复。

后端不可用时，本次集成不自动回退到 mock 数据；UI 应展示错误和重试入口。Android 已接入上传、识图和语音录音转写，真实语音 provider 仍依赖可被外部 ASR 访问的音频 URL。

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

RAG 检索质量通过 `data/rag_eval/` 下的 profile 评测集跟踪。运行 `python -m app.scripts.evaluate_rag --profile android-contract` 可验证 Android 合同商品，运行 `python -m app.scripts.evaluate_rag --profile demo` 可验证演示商品，运行 `python -m app.scripts.evaluate_rag --profile beta-fixture --retrieval vector` 可用 beta fixture 重建临时 Chroma 索引并评估真实召回链路。fallback 评测使用生产 RAG pipeline 的二阶段 rerank 装配。报告包含 `recall@k`、`top1_accuracy`、`mrr@k`、当前失败案例和 case-level diagnostics；失败行会直接打印 source、fallback stage、candidate IDs、final IDs 和 filter reasons。`tests/test_rag_eval.py` 对固定评测集提供轻量回归门禁。运行 `python -m app.scripts.check_vector_index --profile demo` 可检查演示索引缺失或陈旧商品 ID。

`POST /api/v1/rag/search` 的响应结构为 `{"query": string, "items": RagItem[], "total": number}`。`RagItem` 字段为 `product_id`、`name`、`price`、`score`、`reason`、`category`、`platform`、`product_url` 和 `stock_status`；额外字段不属于长期 API 契约。
