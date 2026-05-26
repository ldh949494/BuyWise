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

当前 Android 集成覆盖商品浏览、商品详情、商品对比、AI 导购流式输出、固定资源多模态联调、商品详情记录购买、首页待评价提示和内联反馈表单。

多模态页面只使用内置演示图片和音频 bytes 调用后端上传、识图和语音接口，不申请相机、相册或麦克风权限，也不做本地转码。订单反馈表单支持评分、内容、优点标签、缺点标签和是否符合预期。缺少 `BUYWISE_BETA_TOKEN` 时，购买和反馈入口会在 UI 层提前禁用并展示 token 提示。
