# 设计：Android 悬浮决策组件质感

Status: Draft

## 背景

BuyWise Android 端需要在卡片式组件、关键入口和高价值模块上增强触感和层级，但产品仍然是购物决策工具。视觉参考采用柔和悬浮卡片、纯色拟磨砂面板和轻微下压反馈，不能削弱商品名、价格、评分、库存和推荐理由的可读性。

## 方案

该风格扩展到 Android 端所有卡片式组件和主要入口容器，包括首页、导购、需求提取、推荐商品、商品详情、对比、识图联调、反馈、聊天推荐小卡和悬浮对比篮。标准控件本身（输入框、按钮、聊天气泡、底部输入栏）保留 Material/聊天语义，只在外层容器或卡片式入口上增强质感。

组件层新增轻量 `FloatingGlassCard`：

- 使用半透明面板色、浅色边框和克制阴影模拟磨砂质感，不默认使用真实背景模糊。
- 支持 `Neutral`、`Primary`、`Warm`、`Success`、`SolidPrimary` tone，主操作仍保留现有品牌主色。
- 可点击卡片提供明确但克制的真实下压反馈，按下时缩放到约 `0.965`、下移约 `2dp`、阴影收紧。
- 动效读取系统动画缩放设置；关闭系统动画时保留状态变化但取消缩放位移。
- 支持横向小卡片禁用全宽填充，适配推荐小卡、对比候选条和胶囊入口。

视觉约束：

- 购物决策效率优先，高级感作为包装。
- 商品名、价格、评分、库存、推荐理由和对比状态必须保持高对比。
- 纯色磨砂用于状态标签、首推条、输入入口、已加入对比状态、对比篮入口和关键工具入口。
- 功能化装饰可以服务状态表达，不引入圆球、波浪或独立漂浮装饰。
- 普通长列表商品卡可以使用统一悬浮容器，但状态色只在首推、已加入对比、警告或成功反馈等有意义状态出现。

## 影响

影响 Android Compose UI：

- `android-app/app/src/main/java/com/buywise/android/ui/components/FloatingGlassCard.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/components/ShopComponents.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/components/FloatingCompareBasket.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/GuideScreen.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/GuideDemandPanel.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/Screens.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/HomePanels.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/ComparePanels.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/CompareVisionScreens.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/VisionPanels.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/ProductDetailScreen.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/FeedbackPromptCard.kt`
- `android-app/app/src/main/java/com/buywise/android/ui/screens/GuideChatScreen.kt`

不影响后端 API、repository、model 或数据结构。

## 验证

- 运行 Android Gradle 构建或 `:app:assembleDebug` 验证 Compose 编译。
- 运行仓库自动校验，确保文档、provider、repo lint、entropy 和后端测试仍通过。
- 手动检查首页、导购页、对比页、识图页、商品详情页、反馈卡和对话导购：卡片式容器统一悬浮质感，点击反馈明确且不影响文字和关键商品数据阅读。

## 最近检查

2026-06-03
