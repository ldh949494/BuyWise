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
- BuyWise 使用轻量自建组件层，不引入大而全第三方 UI 库。
- 可复用视觉和业务组件放在 `ui/components/`，screen 只负责页面编排和状态接线。
- 商品卡、聊天推荐卡、标签、浮层卡片、对比篮、错误/空状态等重复样式应先沉淀为组件，再在页面中复用。
- 新增组件应优先复用 `BuyWiseTheme`、`BuyWiseDimens`、`FloatingGlassCard`、`TactileIconTile` 和 Material 3 基础控件。
- 页面不应直接堆叠临时 `Surface + Icon` 样式；关键入口、空状态、AI/视觉/语音/对比等图标先从 `BuyWiseIcons` 语义资产中取，再按场景放入 `TactileIconTile`。
- 触感悬浮风格只用于关键入口、高价值模块和可点击状态反馈；普通文本、商品证据、价格、理由和表单保持干净直接。
- 后端地址必须兼容模拟器访问宿主机的 `http://10.0.2.2:8000`。
- 导购页使用流式状态展示回复，不应退回纯本地 mock。

## 验证

本地工具可用时运行：

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

后端或文档单独改动时，仓库验证脚本可以跳过 Android 构建。
