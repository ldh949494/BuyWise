# Frontend Requirements Checklist

本文档给前端团队使用，描述基于当前 BuyWise 后端能力应实现的页面、交互、状态和联调验收清单。

## Scope

当前前端优先服务 BuyWise MVP：商品浏览、商品详情、商品对比、AI 导购、多模态输入和基础错误处理。

暂不把后台商品创建作为用户侧核心功能；如需管理台，可单独规划。

## Runtime Requirements

- [ ] 支持配置 API Base URL，默认本地为 `http://localhost:8000`。
- [ ] Web 本地开发端口应使用后端 CORS 默认白名单中的 `3000` 或 `5173`，否则同步更新后端配置。
- [ ] Android 模拟器访问后端时使用 `http://10.0.2.2:8000`。
- [ ] 所有 API 请求统一经过请求客户端，集中处理 base URL、JSON header、错误解析和 request ID。
- [ ] 支持把 `X-Request-ID` 写入请求头，并在错误日志中保留。
- [ ] 文件上传请求使用 `multipart/form-data`，字段名为 `file`。

## Data Model Requirements

- [ ] 定义 `Product` 模型，覆盖 `id`、`name`、`category`、`brand`、`sku`、`price`、`original_price`、`platform`、`product_url`、`image_url`、`image_urls`、`rating`、`sales`、`description`、`specs`、`tags`、`suitable_scene`、`stock`、`stock_status`、`review_summary`、`created_at`、`price_history`。
- [ ] 商品字段按可空处理，尤其是价格、评分、库存、图片、规格、历史价格。
- [ ] 定义 `CompareResult` 模型，覆盖 `items`、`summary`、`winner_id`。
- [ ] 定义 `ChatMessage` 和 `ChatResponse` 模型，支持文本、商品卡片、追问、结构化需求。
- [ ] 定义统一 `ApiError` 模型，覆盖 `detail`、`code`、`extra.request_id`。

## Product Browse

- [ ] 商品列表页调用 `GET /api/v1/products`。
- [ ] 支持按 `category` 筛选。
- [ ] 支持按 `keyword` 搜索。
- [ ] 支持 `price_min`、`price_max` 价格筛选。
- [ ] 支持分页参数 `page`、`page_size`。
- [ ] 列表展示商品图、名称、品牌、价格、原价、评分、标签、库存状态。
- [ ] 空结果展示明确空状态。
- [ ] 加载中状态避免重复提交。
- [ ] 请求失败时展示 `detail`，并保留 `request_id` 便于排查。

## Product Detail

- [ ] 商品详情页调用 `GET /api/v1/products/{product_id}`。
- [ ] 展示图片、名称、品牌、价格、评分、描述、标签、适用场景、规格、库存、评价摘要。
- [ ] `specs` 支持对象、数组或空值的动态渲染。
- [ ] `price_history` 有数据时展示价格趋势；无数据时隐藏。
- [ ] 商品不存在时处理 `404 not_found`，展示不存在或已下架状态。
- [ ] 支持从详情页加入对比。

## Product Compare

- [ ] 支持从列表或详情选择 2 个或多个商品进入对比。
- [ ] 调用 `POST /api/v1/products/compare`，请求体包含 `product_ids` 和可选 `user_need`。
- [ ] 展示对比摘要 `summary`。
- [ ] 使用 `winner_id` 高亮推荐商品。
- [ ] 对比表展示价格、评分、分数、规格、优点、缺点。
- [ ] `pros`、`cons` 为空时隐藏对应区块。
- [ ] 从对比项跳转详情时优先使用 `product_id`，为空时回退到 `id`。
- [ ] 用户需求为空时仍可发起基础对比。

## AI Guide

- [ ] AI 导购页调用 `POST /api/v1/ai/chat`。
- [ ] 支持文本输入。
- [ ] 支持会话 ID 保存和复用，优先使用响应中的 `extra.session_id`。
- [ ] 渲染助手回复 `reply`。
- [ ] 当 `need_clarify=true` 时，将回复作为追问展示，保留用户继续补充输入的状态。
- [ ] 展示 `structured_need` 中的意图、类目、预算、场景、偏好、规避项。
- [ ] 当 `missing_fields` 非空时，前端可提供快捷补充入口。
- [ ] 渲染 `products` 为聊天内商品卡片。
- [ ] 商品卡片展示 `reason`、`budget_match`、`scenario_match`、`conflicts`、`alternatives`。
- [ ] 支持从聊天商品卡片进入详情或加入对比。

## Multimodal Input

- [ ] 图片上传前校验扩展名和 MIME 类型。
- [ ] 音频上传前校验扩展名和 MIME 类型。
- [ ] 上传大小限制按后端默认 `10MB` 做前端预校验。
- [ ] 调用 `POST /api/v1/upload` 时带有 `upload:write` 权限的 Bearer Token。
- [ ] 上传成功后保存返回的 `url`。
- [ ] 图片识别调用 `POST /api/v1/vision/recognize`，参数为 `image_url`。
- [ ] 图片识别结果中的 `query` 可进入商品搜索或 AI chat。
- [ ] 语音识别调用 `POST /api/v1/speech/asr`，参数为 `audio_url`。
- [ ] 语音识别结果中的 `text` 可回填输入框，用户确认后发送给 AI chat。
- [ ] 处理上传 `401`、`413`、`415` 错误，并给出明确提示。

## Error And Empty State Requirements

- [ ] 所有错误统一解析 `{detail, code, extra}`。
- [ ] 表单校验错误 `validation_error` 展示字段级提示或通用提示。
- [ ] 未授权 `unauthorized` 引导检查上传 token 或登录态。
- [ ] 权限不足 `forbidden` 展示无权限提示。
- [ ] 上传过大 `upload_too_large` 展示大小限制。
- [ ] 不支持的上传类型 `unsupported_upload_type` 展示支持格式。
- [ ] 服务端错误 `internal_error` 展示重试入口并记录 request ID。
- [ ] 网络超时、断网和 CORS 失败应有独立提示。

## UX Requirements

- [ ] 首屏直接进入可用购物体验，不做纯营销落地页。
- [ ] 商品列表、详情、对比和 AI 导购之间可互相跳转。
- [ ] AI 导购输入区始终可访问，长回复和商品卡片不应遮挡输入。
- [ ] 对比选择状态在列表和详情之间保持一致。
- [ ] 图片、价格、评分缺失时有稳定占位，不造成布局跳动。
- [ ] 移动端优先保证单手操作：搜索、筛选、聊天输入、加入对比按钮易触达。
- [ ] 商品卡片文字在窄屏不溢出。

## Integration Acceptance

- [ ] `GET /api/v1/health` 可成功探活。
- [ ] `GET /api/v1/products?page=1&page_size=20` 能渲染列表。
- [ ] `GET /api/v1/products/{id}` 能渲染详情。
- [ ] 商品不存在时详情页能处理 `404`。
- [ ] `POST /api/v1/products/compare` 能渲染推荐赢家和对比表。
- [ ] `POST /api/v1/ai/chat` 能渲染回复、结构化需求和商品卡片。
- [ ] 连续发送 chat 时能复用同一个 `session_id`。
- [ ] 上传图片后能调用视觉识别并生成搜索词。
- [ ] 上传音频后能调用 ASR 并生成文本输入。
- [ ] 所有失败请求都能展示 `detail` 并记录 `request_id`。

## Backend Gaps To Track

- [ ] 上传接口当前需要 Bearer Token；前端需要获取测试 token 或后端提供临时上传凭证策略。
- [ ] RAG `items` 当前是开放字典数组，不适合作为强类型生产 UI 的唯一数据源。
- [ ] Vision 和 Speech 当前是预留/模拟能力，前端应保留加载、失败和结果确认流程，避免把模拟返回写死。
- [ ] 商品创建是受保护接口，若需要管理台，需要补充登录、权限和数据录入校验设计。
- [ ] 上传返回相对 URL，部署到不同域名时需要前端统一拼接资源 origin 或后端改为绝对 URL。
