# 设计：P1 订单反馈闭环

Status: Approved

## 背景

BuyWise 当前定位是多模态电商购物 guide，核心能力围绕商品数据、推荐、对比、RAG 和 Android 演示路径。用户希望补齐下单、付款、物流查看以及收货后一段时间发起商品评价反馈的闭环，并将该反馈按一定权重纳入商品分析指标。

P1 不把 BuyWise 扩展为真实交易平台。订单、付款和物流只作为内部体验、状态模型和外部平台引用，用于支撑已购评价、推荐解释和商品分析闭环，不处理真实资金流、库存扣减、履约对账、退款售后或支付合规。

## 方案

P1 建立交易影子模型：后端保存模拟订单和订单项，商品详情或推荐结果可触发“记录购买/模拟购买”。订单项主绑定 BuyWise 内部 `Product.id`，同时保存外部平台、外部订单号、商品链接和成交快照。底层模型支持多商品订单，但 Android 和 API 主路径先暴露单商品模拟购买。

订单在 P1 内嵌支付和物流状态，不拆独立 payment 或 shipment 表。`orders.payment_status` 使用 `unpaid`、`paid`、`cancelled`、`refunded_mock` 等字符串状态，`orders.fulfillment_status` 使用 `pending`、`shipped`、`delivered`、`cancelled` 等字符串状态，并保存 `paid_at`、`shipped_at`、`delivered_at`。状态合法性由 schema 和 service 层枚举约束，数据库字段保存字符串。P1 提供受控 demo 状态推进 API，允许将订单推进到已收货以演示评价链路。

评价触发围绕订单项建模。默认收货后 7 天触发评价，配置项可控制默认延迟天数；订单项进入已收货状态时写入固化的 `feedback_due_at`，避免未来配置变化影响历史订单。待评价提示由后端接口查询，Android 在启动、首页或订单相关入口拉取并展示；P1 不做真实推送。用户可以忽略首页待评价提示，`feedback_prompt_dismissed_at` 记录在订单项上；订单详情仍保留评价入口。

已购反馈复用并扩展现有 `reviews` 表，不新建平行 feedback 表。`reviews` 作为统一口碑事实表，新增 `order_item_id`、`user_ref`、`source`、`verified_purchase`、`rating`、`usage_context`、`pros_tags`、`cons_tags`、`met_expectation`、`status`、`submitted_at`、`updated_at` 等字段。导入评论继续作为 `source=imported`，收货后反馈作为 `source=buywise_post_delivery`。每个订单项最多一条 active 反馈；用户可更新反馈，也可撤回为 `status=withdrawn`，分析只纳入 active 反馈。

反馈表单轻量结构化：`rating` 和 `content` 必填，`rating` 是 1 到 5 的整数，文本有最小长度限制；`sentiment` 默认由评分推导，4 到 5 为 positive，3 为 neutral，1 到 2 为 negative。`usage_context`、`pros_tags`、`cons_tags`、`met_expectation` 可选。优缺点标签使用后端允许的固定 code，Android 展示本地化文案，API 拒绝未知标签。

订单和评价先使用轻量 `user_ref`，不在本阶段建设完整账号登录系统。API 通过 provider 获取当前 subject；如果当前没有真实 auth provider，则使用 demo/default subject。创建已购反馈时必须校验订单项属于当前 `user_ref` 且已经收货，`verified_purchase` 只能由服务端根据订单项判定，客户端不能伪造。

商品分析指标先动态聚合，不建物化 `product_feedback_metrics` 表。服务层产出 `verified_review_count`、`weighted_rating`、`positive_weight`、`neutral_weight`、`negative_weight`、`top_pro_tags`、`top_con_tags`、`expectation_met_rate`、`recent_feedback_count` 和 `feedback_summary`。权重公式写在服务中，关键常量放配置：已购反馈基础权重高于导入评论，收货后 3 到 30 天反馈权重提高，过短文本降权，有结构化标签加权，单条权重设上限。推荐、对比和商品分析全局使用该信号，但权重受限，不能压过预算、品类、库存、适用场景等主约束。全局商品口碑和当前用户个人偏好分开建模，用户自己的反馈额外影响个人化推荐。

Android P1 只做最小闭环，不做完整订单中心。商品详情页增加记录购买或模拟购买入口，创建成功后展示状态摘要；首页或 guide 入口展示待评价提示；评价表单支持评分、文字、场景、优缺点标签和符合预期；商品详情可以展示聚合反馈摘要。

## 影响

- 后端模型：新增 `Order`、`OrderItem`，扩展 `Review`。
- Alembic：新增订单和订单项表，扩展 reviews 字段，增加 `user_ref`、`order_item_id`、`source`、`feedback_due_at` 等索引。
- 后端 schemas：新增订单创建、订单读取、订单项读取、待评价提示、已购评价提交、评价更新和撤回 schema。
- 后端 repositories：新增订单 repository，扩展 review repository 的已购反馈查询、唯一 active 反馈检查和商品反馈聚合。
- 后端 services：新增订单服务、反馈提示服务和评价信号服务，扩展推荐、对比、商品详情和聊天分析中的口碑信号。
- API 路由：新增 `POST /api/v1/orders`、`GET /api/v1/orders`、`GET /api/v1/orders/{order_id}`、`POST /api/v1/orders/{order_id}/advance`、`GET /api/v1/feedback/prompts`、`POST /api/v1/feedback/prompts/{order_item_id}/dismiss`、`POST /api/v1/reviews/from-order-item`、`PUT /api/v1/reviews/{review_id}`、`POST /api/v1/reviews/{review_id}/withdraw`。
- Android：商品详情购买记录入口、待评价提示、评价表单、反馈摘要展示。
- 配置：新增反馈延迟天数、评价权重基础值、时间窗口乘数、内容乘数和单条权重上限。
- 文档：更新 API、配置、Android 边界和演示检查清单。

## 验证

- 模型测试覆盖 `orders`、`order_items` 和扩展 `reviews` schema。
- API 测试覆盖模拟下单、订单状态推进、待评价提示、忽略提示、已购评价提交、更新和撤回。
- 服务测试覆盖非缺货校验、订单项归属校验、已收货校验、`verified_purchase` 服务端判定、重复 active 反馈限制和反馈权重公式。
- 推荐和对比测试覆盖已购反馈信号参与评分但不覆盖预算、品类、场景等主约束。
- Android contract 测试覆盖新增响应字段和待评价提示数据结构。
- 文档验证运行 `python scripts/validate_docs.py`。
- 后端或文档提交前运行 `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`。

## 最近检查

2026-05-23
