# 设计：P3 Android Beta Client

Status: Implemented

## 背景

阶段 3 的目标是把 Android 从 demo client 收敛为 beta client。重点不是重做 UI，而是拆掉单个 `ShopRepository` 和单个 `BuyWiseViewModel` 承担全部职责的结构，并补齐购买后反馈和 beta token 用户体验。

## 方案

迁移采用 façade 方式降低风险。`ShopRepository` 暂时保留为组合入口，但真实 API 能力拆到 `ProductRepository`、`GuideRepository`、`CompareRepository`、`OrderRepository`、`FeedbackRepository` 和 `UploadRepository`。`BuyWiseViewModel` 暂时保留给 `MainActivity` 使用，但内部组合 `HomeViewModel`、`GuideViewModel`、`ProductDetailViewModel`、`CompareViewModel`、`FeedbackViewModel` 和 `UploadViewModel`。

REST JSON 使用 `kotlinx.serialization` 和 DTO，`BuyWiseApiClient` 提供 typed `get`、`post` 和 `postUnit`。SSE chat stream 因事件形态不同，本阶段仍保留少量 `JSONObject` 解析在 `GuideRepository` 内。

反馈表单在首页待评价卡片内联展开，不新增导航页。表单支持评分、内容、优点标签、缺点标签、是否符合预期，并在 `FeedbackViewModel` 中维护 per-item draft、提交中、失败和成功状态。

`BUYWISE_BETA_TOKEN` 被建模为 `BetaCapability`。缺 token 时商品详情的记录购买按钮提前禁用，首页反馈区域显示明确提示且不请求待评价列表；repository 仍保留缺 token 异常兜底。

## 验证

- Android debug build：`.\gradlew.bat :app:assembleDebug`
- Repository lint：`python scripts/validate_repo_lint.py`
