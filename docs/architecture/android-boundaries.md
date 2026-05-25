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

当前 Android 集成覆盖商品浏览、商品详情、商品对比、AI 导购流式输出、固定资源多模态联调、商品详情记录购买、首页待评价提示和一键提交固定内容评价。

多模态页面只使用内置演示图片和音频 bytes 调用后端上传、识图和语音接口，不申请相机、相册或麦克风权限，也不做本地转码。订单反馈仍是部分闭环：Android 已能记录购买、拉取待评价提示并提交固定内容评价，完整评价表单、可选标签/场景输入和反馈摘要展示仍属于后续工作。
