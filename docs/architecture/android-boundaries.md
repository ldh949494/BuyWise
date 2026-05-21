# Android 边界

Android 客户端位于 `android-app/`，是原生 Kotlin 应用。

## 当前形态

- 构建系统：Gradle Kotlin DSL。
- UI：Jetpack Compose 和 Material 3。
- 架构风格：MVVM；`ViewModel` 协调状态，`data/` 下的 repository 通过 OkHttp 对接 Android 合同流。
- 主包路径：`android-app/app/src/main/java/com/buywise/android/`。

## 边界说明

- 页面放在 `ui/screens/`。
- 复用组件放在 `ui/components/`。
- 页面状态和用户动作由 `viewmodel/` 协调。
- 数据模型和 repository 行为放在 `data/`。

## 后端连接

模拟器访问宿主机后端时使用 `http://10.0.2.2:8000`，该地址通过 Android `BuildConfig.BUYWISE_API_BASE_URL` 配置。Android 变更必须兼容 `docs/reference/api.md` 中记录的后端 API。

当前 Android 集成覆盖商品浏览、商品详情、商品对比和 AI 导购流式输出。识图、上传和语音页面仍是本地演示，等待后续实现端到端媒体链路。
