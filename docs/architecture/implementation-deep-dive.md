# 架构设计与代码实现说明

本文档面向需要理解、维护或扩展 BuyWise 的开发者，集中说明系统架构设计、代码分层、核心业务链路和关键实现细节。短版边界说明见 `docs/architecture/system-overview.md`、`docs/architecture/backend-boundaries.md` 和 `docs/architecture/android-boundaries.md`；本文档是代码实现层面的深读。

## 1. 系统定位

BuyWise 是一个多模态电商购物导购系统，仓库同时包含 FastAPI 后端和原生 Android 客户端。当前产品重点不是完成真实电商交易，而是围绕“商品理解、AI 导购、商品对比、购买记录、已购评价反馈”形成一个可演示、可测试、可迭代的闭环。

系统的主要职责如下：

- 后端提供版本化 REST API、SSE 流式导购接口、商品数据库访问、RAG 检索、推荐排序、订单和评价闭环、上传/视觉/语音能力。
- Android 客户端提供用户侧购物导购体验，包括首页商品、AI 导购聊天、商品详情、对比篮、购买记录、待评价提醒和反馈表单。
- 向量索引和 LLM 能力作为可替换外部能力接入，代码中通过 gateway、service、provider 和依赖容器降低耦合。
- 运行时通过 provider 统一接入日志、错误、认证、遥测和请求上下文，避免业务层直接绑定横切实现。

## 2. 顶层架构

当前端到端主链路可以概括为：

1. Android 用户输入购物需求，或者从演示图片、语音流程追加识别文本。
2. Android `GuideRepository` 调用 `/api/v1/ai/chat/stream` 创建 SSE 连接。
3. FastAPI 路由层接收 `ChatRequest`，从依赖容器取出 `ChatService`。
4. `ChatService` 和 `ChatStreamRunner` 抽取结构化需求，调用 RAG pipeline 召回商品，再调用推荐排序。
5. 后端先以 `products` SSE 事件返回商品卡片或 `bundle_plans` 方案卡片，再以 `token` 事件流式返回 LLM 文案，最后发送 `done`。
6. Android `GuideViewModel` 把 SSE 事件转换为 Compose 可观察状态，页面增量展示回复、推荐卡片或组合方案卡片。

整体依赖方向如下：

```text
Android UI -> Android ViewModel -> Android Repository -> HTTP/SSE
HTTP/SSE -> FastAPI route -> Service -> Repository / AI / VectorStore / Integration
Repository -> SQLAlchemy model -> Database
AI / VectorStore / Integration -> external provider or local fallback
```

依赖方向是架构约束。路由层可以依赖服务层，服务层可以组合 repository、AI、vector store 和 integration，repository 只依赖数据库模型和 session。低层模块不得反向导入 API 路由，也不应绕过 provider 直接绑定横切实现。

## 3. 后端应用启动与依赖装配

后端入口是 `app/main.py`。`create_app()` 完成以下工作：

- 调用 `settings.validate_production()` 校验生产配置。
- 通过 `get_logging_provider().configure()` 初始化日志。
- 创建 `FastAPI` 实例，配置标题、debug、版本、OpenAPI 路径和 lifespan。
- 安装应用容器构建器，注册 CORS 和自定义中间件。
- 将 `app/api/router.py` 中的 `api_router` 统一挂载到 `settings.api_v1_prefix`，默认是 `/api/v1`。
- 尝试挂载 `admin-web/dist` 到 `/admin`，用于内部后台静态页面。
- 注册全局异常处理和遥测 instrumentation。

应用级对象由 `app/core/dependencies.py` 管理。`AppContainerBuilder.build()` 会创建或注入这些对象：

- `Settings`
- SQLAlchemy `session_factory`
- `LLMClient` 或其他 `AIModelGateway`
- `ChromaProductStore` 或其他 `VectorRetrievalGateway`
- `RAGPipeline`
- `RagService`
- `CompareService`
- `ChatService`
- `UploadService`
- `SpeechService`
- `VisionService`
- `ReadinessService`

这种容器不是完整 IoC 框架，而是一个轻量、显式的应用作用域对象集合。它的主要价值是：

- 测试可以通过 `AppContainerBuilder.with_*()` 注入 fake LLM、fake vector store 或独立 session factory。
- 长生命周期资源，例如 vector store，可以在 lifespan 结束时统一关闭。
- 路由层通过 `Depends(get_chat_service)`、`Depends(get_rag_service)` 等函数获取服务，不直接构造复杂依赖。

## 4. API 路由组织

路由聚合入口是 `app/api/router.py`。它把以下模块统一注册到 `api_router`：

- `admin.py`：内部后台。
- `auth.py`：普通用户 OTP 登录、刷新和退出。
- `health.py`：健康检查和 readiness。
- `products.py`：商品浏览和维护。
- `orders.py`：内部模拟订单。
- `feedback.py`：待评价提示。
- `reviews.py`：已购评价。
- `compare.py`：商品对比。
- `chat.py`：AI 导购 JSON 和 SSE。
- `rag.py`：公开 RAG 搜索。
- `upload.py`、`vision.py`、`speech.py`：多模态相关接口。

路由层原则是“薄”：它负责 HTTP 契约、`Depends` 注入、认证检查、状态码和 Pydantic 响应模型，不承载复杂业务规则。复杂规则应放入 `app/services/`。

## 5. 数据模型、Schema 与 Repository

BuyWise 后端使用 SQLAlchemy ORM 作为持久化模型，Pydantic schema 作为 API 合同。

典型对象分工：

- `app/models/product.py` 中的 `Product` 是数据库模型，包含商品名称、类目、品牌、SKU、价格、平台、链接、图片、评分、销量、描述、规格、标签、适用场景、库存状态、评价摘要等字段。
- `app/schemas/product.py` 定义商品创建、更新、读取和列表响应的 API 形状。
- `app/repositories/product_repo.py` 负责 SQLAlchemy 查询、分页、过滤、软下架和 SKU upsert。
- `app/services/product_service.py` 负责业务规则、事务提交、响应前字段归一化、评价/价格信号挂载和向量索引更新。

Repository 的事务边界有明确约束：repository 可以查询、`add`、`flush`、`refresh`，但不负责 `commit()` 或 `rollback()`。完整用例的提交和回滚由 service 或脚本入口处理。代码中通过 `app/core/transaction.py` 的 `unit_of_work()` 管理提交、刷新和异常回滚。

商品软下架不是删除数据库行，而是将 `stock_status` 设置为 `discontinued`、`stock` 设置为 `0`。公开商品浏览、详情、RAG、推荐和对比默认过滤这类商品。

## 6. 商品能力实现

商品 API 的核心实现由 `ProductService` 驱动。

### 6.1 商品读取

`ProductService.get_product()` 使用 `ProductRepository.get_by_id()` 读取商品。如果不存在或默认不可见，抛出 `AppError(status_code=404, code="not_found")`。读取后服务会做几类补充：

- 归一化 JSON 列表字段，例如 `tags`、`suitable_scene`、`image_urls`，避免响应层看到 `None`。
- 根据库存数量推导 `stock_status`。
- 加载 `PriceHistoryRepository.list_for_product()` 的价格历史。
- 如果商品没有 `review_summary`，通过 `ReviewRepository.build_summary_for_product()` 构造摘要。
- 用 `ReviewSignalService` 挂载反馈指标。

### 6.2 商品列表

`ProductService.list_products()` 对分页参数做防御性修正：`page >= 1`，`page_size` 限制在 `1..100`。底层 repository 支持类目、关键词、最低价、最高价和是否包含下架商品。关键词会在商品名、描述和品牌中做 `ilike` 匹配。

### 6.3 商品写入与索引同步

创建、更新、软下架和 SKU upsert 都由 service 开启 `unit_of_work()`。事务提交后调用 `_after_write_commit()`：

- 归一化商品字段。
- best-effort 更新向量索引。
- 记录结构化日志。

索引更新失败不会回滚商品数据库写入，因为商品写入是主事实源，向量索引可以通过脚本重建或 upsert 修复。这是一个有意设计：保证管理侧商品维护不被可恢复的检索索引故障阻塞。

## 7. AI 导购实现

AI 导购有两个 HTTP 入口：

- `POST /api/v1/ai/chat`：非流式 JSON 响应，适合测试、兼容和调试。
- `POST /api/v1/ai/chat/stream`：SSE 流式响应，是 Android 主链路。
- `GET/PUT/DELETE /api/v1/guide/preferences`：普通用户账号级导购偏好管理。

导购偏好由 `GuidePreferencesService` 负责管理和应用。chat 路由可选读取普通用户 principal；未登录请求仍可导购，但只使用本次输入和临时偏好。服务按“本次输入 > 临时偏好 > 账号偏好 > 系统默认”的顺序补齐预算策略、预算上限、偏好标签、排除项和已有设备，并返回 `applied_preferences` 给前端展示。

两者都由 `app/api/v1/chat.py` 接入，核心业务由 `ChatService` 和 `ChatStreamRunner` 完成。

### 7.1 非流式导购

`ChatService.handle_chat()` 的主要步骤：

1. 根据请求中的 `session_id` 获取或创建聊天会话。
2. 合并文本、语音转写结果和图片识别结果。
3. 加载历史消息中最近一次结构化需求，作为上下文补全当前需求。
4. 保存用户消息。
5. 调用 `IntentService.extract()` 抽取 `StructuredNeed`。
6. 如果需求需要澄清，调用 LLM 生成澄清问题并返回空商品列表。
7. 如果需求明确，调用 `_rank_recommendations()` 完成召回和排序。
8. 调用 LLM 生成最终推荐文案。
9. 保存 assistant 消息和推荐记录，提交事务。
10. 返回 `ChatResponse`，其中 `extra.session_id` 是客户端后续续聊的会话标识。

容量受限时，`ChatService` 会识别 LLM capacity 类异常，记录 `buywise_llm_failures_total`，并返回基础推荐 fallback 文案。其他运行时异常会回滚聊天写入，并返回“暂时无法完成推荐”的兜底回复。

### 7.2 流式导购

流式入口 `stream_chat()` 返回 `StreamingResponse(media_type="text/event-stream")`。路由层包装了 `_stream_with_keepalive()`：

- 后端业务迭代器长时间没有事件时发送 `heartbeat`。
- 总耗时超过 `settings.chat_stream_max_seconds` 时发送 `error`，code 为 `chat_stream_timeout`。
- 业务事件发送 `done` 或 `error` 后结束流。
- 关闭流时取消未完成 task，并尝试调用 async iterator 的 `aclose()`。

`ChatStreamRunner.generate_events()` 负责产生业务事件，主要事件顺序是：

```text
meta -> status(intent) -> status(retrieval) -> products -> status(generation) -> token* -> done
```

如果需求需要澄清，则事件序列变成：

```text
meta -> status(intent) -> status(generation) -> token* -> products(empty) -> done
```

如果 LLM 生成阶段容量受限，则不长期暴露独立 fallback 事件，而是：

```text
status(fallback) -> done(degraded=true, degraded_reason=llm_capacity_limited)
```

### 7.3 快速商品路径

`ChatStreamRunner` 有一条 fast products 路径，用于首轮、纯文本、无图片/语音、无历史消息且数据库 session 可用的场景。该路径通过 `IntentService.extract_by_rules()` 做规则抽取，如果能得到类目，就直接走 `ProductRepository.list_products()` 拉取商品并排序，减少首个商品卡片延迟。

fast path 的价值是让 Android 尽快展示商品卡片；当 fast DB 没有结果时，会回退到完整 RAG pipeline。

## 8. RAG 检索与推荐排序

BuyWise 当前有两个 RAG 使用面：

- `RagService`：服务公开 API `/api/v1/rag/search`，返回 `RagSearchResponse` 和强类型 `RagItem`。
- `RAGPipeline`：服务聊天推荐内部链路，返回 SQLAlchemy `Product` 列表，并挂载评价、反馈和价格信号供排序使用。

### 8.1 公开 RAG 搜索

`RagService.search()` 先调用 `ChromaProductStore.search()` 做向量检索。向量结果只作为候选 ID 和分数来源，服务会回查数据库刷新商品事实字段，避免返回已经删除、下架、价格过期或库存不可用的索引脏数据。

向量结果过滤规则包括：

- 商品 ID 在数据库不存在：`stale_index`。
- 类目不匹配：`category_mismatch`。
- 超预算：`over_budget`。
- 缺货或下架：`unavailable`。

如果向量检索失败或没有有效结果，`RagService` 使用 `ProductRepository.list_products()` 做数据库 fallback，并记录 RAG fallback 和空结果指标。

### 8.2 聊天 RAG Pipeline

`RAGPipeline.search_products_sync()` 的流程更复杂：

1. 用 `build_query_from_need()` 将结构化需求转换为检索 query。
2. 向量检索候选，候选数量为 `max(top_k * 3, 30)`。
3. 从向量结果提取商品 ID，按向量顺序回查数据库。
4. 如果向量没有候选，按类目和预算从数据库拉取 fallback 候选。
5. 使用 `RagFilterPolicy` 进行严格过滤。
6. 如果严格过滤后为空，按 `RagFallbackPolicy` 尝试放宽预算、放宽条件和相邻类目。
7. 挂载评价情感计数、反馈指标和价格历史均值。
8. 使用 `RagRerankPolicy` 或可注入 reranker 重新排序。
9. 记录 diagnostics，包括 source、fallback_stage、filter_reasons、retrieved_ids、candidate_ids、final_ids 和 latency。

聊天层随后再通过 `RecommendService.rank()` 或 `BundleRecommendService.rank()` 进行业务排序和结果截断。普通推荐默认 balanced 策略召回 20 个、返回 5 个；explore 策略召回 30 个、返回 8 个；strict 策略召回 12 个、返回 5 个。

## 9. 商品对比实现

商品对比入口是 `/api/v1/products/compare`。路由层接收商品 ID 和可选 `user_need`，服务层读取商品并生成对比结构。

对比能力的实现原则是：

- 对比的输入是明确商品 ID，不重新做召回。
- 商品事实字段来自数据库，不依赖 Android 缓存。
- LLM 只用于生成摘要或解释，不应成为商品事实来源。
- 当 LLM 不可用时，对比仍应尽可能返回基础结构化结果。

Android 侧通过对比篮维护最多 4 个商品，`CompareBasketState` 会拒绝非数字 ID 和超过上限的商品。开始对比时调用后端 compare API，并把结果转换成 `CompareState` 的商品列表、对比行、摘要和 winner。

## 10. 订单与已购评价闭环

BuyWise 的订单是内部交易影子模型，用于演示“购买后反馈”闭环，不代表真实支付、真实发货或真实平台履约。

### 10.1 订单创建

`OrderService.create_order()` 的流程：

1. 检查商品存在、未缺货且有价格。
2. 根据是否存在 `external_platform` 判断是否是 closed beta 外部购买记录。
3. 调用 `OrderStateMachine.build_initial_order_state()` 生成付款、物流和反馈到期状态。
4. 构造 `Order` 和 `OrderItem`。订单项会保存商品名、平台、链接和成交价快照。
5. 使用 `unit_of_work()` 写入数据库。
6. 记录 `buywise_order_created_total`。

`APP_ENV=prod` 时订单接口必须有用户 JWT 和对应 scope；dev/test 可以使用 `DEMO_USER_REF` 演示身份。

### 10.2 待评价提示

`OrderService.list_due_feedback_prompts()` 读取当前用户已到期且未提交/未忽略的订单项，返回 `FeedbackPromptRead`。如果有提示，会记录 `buywise_feedback_prompted_total`。Android 首页用这些提示渲染内联反馈入口。

### 10.3 已购评价

`ReviewWorkflowService.create_from_order_item()` 保证评价来自当前用户的已收货订单项：

- 找不到订单项返回 404。
- 订单未 delivered 返回 409。
- 同一个订单项已有 active feedback 返回 409。
- 写入 `Review` 后设置 `item.feedback_submitted_at`。
- 评价包含评分、内容、优缺点标签、是否符合预期、来源、购买证据和状态。

当前购买证据为 `buywise_recorded`，不声明平台验真。评价 sentiment 根据评分推导：4 分及以上为 positive，3 分为 neutral，低于 3 分为 negative。

## 11. 多模态能力

多模态接口由上传、视觉和语音三部分组成：

- `POST /api/v1/upload`：上传文件，需要 `upload:write` scope。
- `POST /api/v1/vision/recognize`：根据图片 URL 或上传结果识别商品信息。
- `POST /api/v1/speech/asr`：根据音频 URL 或上传结果做语音识别。

后端将具体外部服务放在 `app/integrations/` 和 service 中封装，聊天链路只通过 `VisionService.extract_image_info()` 和 `SpeechService.extract_transcript()` 获取结构化信息或文本。这样 AI 导购不直接关心 COS、视觉模型或 ASR 的具体接入方式。

Android 可从相册图片、拍照图片和麦克风录音调用这些接口。语音输入在客户端申请 `RECORD_AUDIO` 权限，录制 m4a 音频后上传，再由 `/api/v1/speech/asr` 转写。识别结果会追加到导购输入框，作为下一次聊天请求的文本上下文。

## 12. Android 客户端架构

Android 代码位于 `android-app/app/src/main/java/com/buywise/android/`，使用 Kotlin、Jetpack Compose 和 Material 3。

核心分层如下：

- `ui/screens/`：页面级 Compose。
- `ui/components/`：复用组件，例如商品卡、反馈卡、浮动对比篮。
- `viewmodel/`：页面状态和用户动作协调。
- `data/`：DTO、domain model、repository、HTTP client、SSE parser 和 mapper。

### 12.1 Repository Facade

`ShopRepository` 是当前 Android 数据层 façade。它持有一个 `BuyWiseApiClient`，并拆分出更细的 repository：

- `ProductRepository`
- `GuideRepository`
- `CompareRepository`
- `OrderRepository`
- `FeedbackRepository`
- `UploadRepository`
- `AuthRepository`

`BuyWiseApiClient` 负责：

- 拼接 `BuildConfig.BUYWISE_API_BASE_URL`。
- 使用 `kotlinx.serialization` 处理常规 JSON DTO。
- 使用 OkHttp 执行请求。
- 在需要鉴权的接口加 `Authorization: Bearer <token>`。
- 对上传接口构造 multipart body。
- 为导购流式接口构造 `/api/v1/ai/chat/stream` POST 请求。

`BUYWISE_BETA_TOKEN` 或登录后的 user access token 控制订单、反馈、上传等用户能力。缺少 token 时，Android 会在 UI 层提前禁用相关入口或显示提示。

### 12.2 ViewModel 状态

`BuyWiseViewModel` 是迁移 façade，内部组合多个子 ViewModel：

- `HomeViewModel`
- `GuideViewModel`
- `CompareViewModel`
- `ProductDetailViewModel`
- `FeedbackViewModel`
- `UploadViewModel`
- `AccountViewModel`

每个子 ViewModel 管理自己的 `mutableStateOf` 状态，Compose 页面通过只读属性读取这些状态。`BuyWiseViewModel` 负责跨页面协调，例如：

- 首页加载商品后刷新待评价提示。
- 商品详情记录购买后刷新待评价提示。
- 识图/语音识别结果追加到导购输入框。
- 登录成功后刷新反馈提示。
- 从商品详情、导购推荐、对比结果或上传结果中查找缓存商品。

### 12.3 SSE 事件处理

`GuideRepository` 使用 OkHttp SSE 创建事件源，并把后端事件转换成 sealed interface `ChatStreamEvent`：

- `Meta`
- `Status`
- `Token`
- `Products`
- `Done`
- `Error`
- `Heartbeat`

`GuideViewModel` 收到事件后切回主线程更新状态：

- `meta` 保存 `sessionId`。
- `status` 更新 `intentSummary`。
- `token` 追加到工作台 `partialReply` 或聊天 assistant 消息。
- `products` 更新推荐商品和组合方案，并在聊天模式下挂到当前 assistant 消息。
- `done` 用完整 reply 补偿 token 拼接结果，并结束 streaming 状态。
- `error` 设置错误信息并结束 streaming。
- `heartbeat` 不改变 UI。

这一设计使后端可以先返回商品卡片或组合方案卡片，再慢慢生成自然语言解释；Android UI 不需要等 LLM 完整结束才展示推荐。

## 13. 认证、错误、日志与遥测

横切能力集中在 `app.core.providers` 及其 provider 实现中。代码约定要求认证、日志、遥测、错误处理和请求上下文都通过 provider 访问，避免业务代码直接依赖具体实现。

认证分为几类：

- 公开接口：商品浏览、商品详情、商品对比、AI 聊天、RAG 搜索、视觉和语音。
- API key/scope 接口：商品写入、上传等维护能力。
- 普通用户 JWT：订单、待评价、评价、上传。
- 管理员 JWT：`/api/v1/admin/...`。
- Readiness token：生产环境 `/api/v1/ready`。

错误处理使用 `AppError` 表达业务错误和 HTTP 状态码。全局错误 provider 负责把异常转换为一致响应。日志通过结构化 extra 输出业务上下文，例如 session、商品 ID、fallback stage、latency 和 filter reasons。指标通过 `app/core/metrics.py` 输出到 `/metrics`，Prometheus label 必须保持低基数。

## 14. 可观测性与诊断

关键运行指标包括：

- 聊天端到端耗时：`buywise_chat_latency_seconds`。
- SSE 首批商品和完成耗时。
- LLM 失败计数：`buywise_llm_failures_total`。
- RAG fallback 和空结果计数。
- 上传失败计数。
- 订单创建、反馈提示、反馈提交成功/失败计数。

RAG 和聊天链路会记录 diagnostics，包含召回来源、fallback 阶段、过滤原因、候选 ID、最终 ID 和延迟。排查推荐质量时，应优先看这些结构化日志，而不是只看最终回复文案。

后台维护任务不在 FastAPI 进程中运行常驻 scheduler。上传 TTL 清理、向量索引检查、索引 upsert/rebuild 都通过脚本和外部调度执行。

## 15. 测试与质量门禁

仓库测试按风险面组织：

- API 合同测试验证 FastAPI 路由响应形状。
- Android 合同测试锁定 Android 依赖字段。
- RAG pipeline 和评测测试验证召回、fallback、排序和 diagnostics。
- schema/model 测试验证 Pydantic 与 SQLAlchemy 契约。
- provider/lint/entropy 脚本阻止横切能力绕路、结构漂移和文档质量问题。

修改代码后应运行相关测试。后端或文档变更提交前运行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

修改文档时运行：

```powershell
python scripts/validate_docs.py
```

修改 provider、认证、日志、错误、遥测或请求上下文时运行：

```powershell
python scripts/validate_providers.py
```

修改结构性边界或新增模块时，补充运行：

```powershell
python scripts/validate_repo_lint.py
python scripts/validate_entropy.py
```

## 16. 扩展新能力的落点

新增后端功能时优先沿用既有分层：

- 新 HTTP 合同放到 `app/api/v1/`，并在 `app/api/router.py` 注册。
- 新业务流程放到 `app/services/`。
- 新数据库访问放到 `app/repositories/`。
- 新 ORM 对象放到 `app/models/`，并配套迁移。
- 新请求/响应合同放到 `app/schemas/`。
- 新外部服务客户端放到 `app/integrations/` 或对应 gateway。
- 新 Android 页面放到 `ui/screens/`，复用 UI 放到 `ui/components/`，状态协调放到 `viewmodel/`，网络和 DTO 放到 `data/`。

新增跨切能力时不要直接在业务服务中散落实现，应先判断是否属于 provider、middleware、dependency 或 container 的职责。

新增 AI/RAG 能力时应保持事实源清晰：

- 商品事实来自数据库。
- 向量索引用于召回，不作为最终事实源。
- LLM 用于需求理解、解释和总结，不作为库存、价格、购买状态或评价真实性的事实源。
- Android 缓存用于 UI 体验，不作为后端权限或商品状态判断依据。

## 17. 维护原则

BuyWise 当前架构的核心原则是：

- 边界清楚：路由、服务、repository、模型、schema 和客户端层各司其职。
- 事实源明确：数据库是商品、订单和评价事实源；向量索引和 LLM 都是辅助能力。
- 可降级：RAG 可从向量回退数据库，LLM 容量受限时可返回基础推荐，SSE 有 heartbeat 和 timeout。
- 可测试：依赖容器允许注入 fake provider，API 和 Android 合同有测试约束。
- 可观测：主链路记录低基数指标和结构化 diagnostics。
- 渐进演进：当前 façade 和 fallback 是迁移中的兼容层，新增代码应优先复用既有边界，确有必要再拆分。

当代码结构、业务闭环或 API 合同发生变化时，应同步更新本文档以及更短的边界文档，避免 `AGENTS.md`、架构说明和真实代码产生漂移。
