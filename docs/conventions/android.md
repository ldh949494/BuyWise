# Android 约定

## 结构

- Kotlin 源码放在 `android-app/app/src/main/java/com/buywise/android/`。
- 页面放在 `ui/screens/`。
- 可复用 Compose 组件放在 `ui/components/`。
- 应用状态和用户动作放在 `viewmodel/`。
- 数据模型、API DTO、repository 行为放在 `data/`。

## UI

- 优先使用项目已经采用的 Material 3 组件。
- 页面聚焦真实应用工作流，不做营销页。
- 后端地址必须兼容模拟器访问宿主机的 `http://10.0.2.2:8000`。
- 导购页使用流式状态展示回复，不应退回纯本地 mock。

## 验证

本地工具可用时运行：

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

后端或文档单独改动时，仓库验证脚本可以跳过 Android 构建。
