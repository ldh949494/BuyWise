# Android 边界

Android 客户端位于 `android-app/`，是原生 Kotlin 应用。

## 当前形态

- 构建系统：Gradle Kotlin DSL。
- UI：Jetpack Compose 和 Material 3。
- 架构风格：MVVM；`BuyWiseViewModel` 和 `ShopRepository` 当前作为迁移 façade，内部已拆分 Home、Guide、ProductDetail、Compare、Feedback、Upload view model 以及 product、guide、compare、order、feedback、upload repositories。
- 主包路径：`android-app/app/src/main/java/com/buywise/android/`。

## 边界说明

- 页面放在 `ui/screens/`。
- 复用组件放在 `ui/components/`。
- 页面状态和用户动作由 `viewmodel/` 协调。
- 数据模型、DTO 和 repository 行为放在 `data/`。REST JSON 使用 `kotlinx.serialization`，SSE chat stream 事件暂保留局部手写解析。

## 后端连接

模拟器访问宿主机后端时使用 `http://10.0.2.2:8000`，该地址通过 Android `BuildConfig.BUYWISE_API_BASE_URL` 配置。Android 变更必须兼容 `docs/reference/api.md` 中记录的后端 API。

当前 Android 集成覆盖商品浏览、场景筛选、首页轻量导购入口、商品详情、商品对比、AI 导购流式输出、图片/语音多模态联调、商品详情记录购买、首页购买后反馈提示和内联反馈表单。

AI 导购页不在客户端判断“追问、刷新、换品类或重新推荐”。`GuideViewModel` 对非对比消息统一调用 guide stream，由后端返回商品、回复、刷新兜底或 action 事件；Android 只负责展示和同步购物车状态。对比页 follow-up 仍走 compare 专用接口。

用户侧主路径以首页为默认入口：搜索服务已知目标，首页导购输入服务需要决策的需求；带 query 进入导购页时由 `BuyWiseViewModel.startGuideFromHome` 自动提交。商品卡、导购结果和详情页优先展示商品名、价格、库存、风险点和证据标签，不把 BuyWise 表达成交易平台。

对比能力由 `CompareBasketState` 和 `FloatingCompareBasket` 承接，用户加入商品后继续停留在当前浏览或导购上下文；悬浮篮显示已选数量，至少 2 件后进入对比页。对比页先展示决策摘要和关键适配，再展示规格矩阵。

多模态页面可从相册、拍照和麦克风录音生成输入，并通过后端上传、识图和语音接口转成导购 query。语音输入会申请 `RECORD_AUDIO` 权限，录制为 m4a 后上传，再调用 `/api/v1/speech/asr`。订单反馈表单支持评分、内容、优点标签、缺点标签和是否符合预期。缺少 `BUYWISE_BETA_TOKEN` 时，购买和反馈入口会在 UI 层提前禁用并展示 token 提示。
