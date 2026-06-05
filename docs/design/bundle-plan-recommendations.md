# 设计：组合方案推荐

Status: Draft

## 背景

BuyWise 当前 AI 导购以单品推荐为主，聊天响应通过 `products: ProductCard[]` 返回候选商品，Android 导购页按线性列表展示推荐结果。这个结构适合“帮我买一个低噪音键盘”，但不适合“帮我配齐一整套电脑”“帮我搭配一整套开学好物”这类多品类购买任务。

组合购买的用户决策目标不是挑一个商品，而是在预算约束下选择一套购买策略。用户需要快速判断整套方案是否配齐、是否超预算、哪些品类待确认、不同预算档多花的钱是否值得，以及方案内商品是否存在搭配风险。

因此组合推荐需要新增方案级展示和方案级数据契约。现有 `ProductCard` 继续服务单品推荐，组合推荐新增 `BundlePlanCard` 作为上层容器，内部复用轻量商品行或商品详情入口。

## 方案

组合推荐作为一等导购结果，由后端返回明确的 `bundle_plans` 字段，Android 根据响应分支渲染方案卡片和方案对比。

### 意图识别

后端意图抽取应区分单品推荐和组合推荐：

- `single_product_recommend`：用户预期输出是单个品类下的候选商品，继续返回 `products` 并使用商品对比。
- `bundle_recommend`：用户预期输出是多个品类组成的商品组合，返回 `bundle_plans` 并使用方案对比。
- `compare`、`clarify` 等其他意图保持独立。

组合推荐触发信号分三层：

- 强触发：一整套、配齐、全套、搭配、套装、清单、开学好物、租房必备、电脑整机加外设。
- 中触发：用户一次提出多个品类，例如电脑、显示器、键鼠、耳机都要。
- 弱触发：场景天然多品类，例如开学、搬家、露营、厨房、宿舍、办公桌面。

组合需求应使用模板优先、LLM 补充的方式生成预期品类。第一版模板：

- 整套电脑/办公桌面，作为首个落地样板。
- 开学好物。
- 租房/宿舍生活小电器。

模板品类分为三类：

- 必选：方案完整度的核心计算对象。
- 可选：可补充但不应强行凑单。
- 需确认：缺失用户约束时应标注，不应假装已经配齐。

当用户信息不足时，默认先给临时方案并标注待确认项；只有总预算或核心用途缺失时才优先追问。

### 响应契约

`ChatResponse` 新增 `bundle_plans: list[BundlePlan]`。`products` 保留作为单品推荐和旧客户端兼容字段。

示例结构：

```json
{
  "reply": "我按预算给你整理了 3 套方案。",
  "structured_need": {
    "intent": "bundle_recommend",
    "category": "整套电脑",
    "budget_max": 6000,
    "scenario": "宿舍学习和轻度游戏"
  },
  "products": [],
  "bundle_plans": [
    {
      "id": "desktop-balanced-6000",
      "title": "方案二 · 6000 元均衡档",
      "budget_tier": "balanced",
      "target_budget": 6000,
      "total_price": 5860,
      "budget_status": "within_budget",
      "budget_delta": -140,
      "recommendation_level": "high",
      "scenario_fit": "宿舍学习、轻度游戏、日常网课",
      "summary": "比入门档更重视显示体验和外设稳定性。",
      "completeness": {
        "included_required": 6,
        "expected_required": 6,
        "optional_included": 2,
        "missing": [],
        "needs_confirmation": ["是否需要正版 Office"]
      },
      "budget_allocation": [
        {"category": "主机", "amount": 3800},
        {"category": "显示器", "amount": 900},
        {"category": "键鼠", "amount": 350}
      ],
      "items": [
        {
          "category": "主机",
          "product": {"id": 1001, "name": "主机 A", "price": 3799},
          "role": "性能核心",
          "required": true,
          "replaceable": true,
          "locked": false,
          "excluded": false
        }
      ],
      "tradeoffs": ["比入门档贵约 900 元，但显示器和电源余量更稳。"],
      "compare_highlights": ["多花的钱主要升级显示器和主机余量。"],
      "exclusion_notes": ["音箱未纳入：耳机已覆盖网课和游戏需求。"],
      "compatibility_checks": [
        {"title": "显示接口", "status": "pass", "message": "主机支持 HDMI/DP。"},
        {"title": "桌面空间", "status": "needs_confirmation", "message": "27 英寸显示器需确认宿舍桌面宽度。"}
      ],
      "price_checked_at": "2026-06-05T14:30:00+08:00",
      "availability_status": "available",
      "revision": 1
    }
  ],
  "extra": {
    "session_id": "s001"
  }
}
```

预算状态规则：

- 默认给 3 个预算档方案：入门、均衡、高配；最多 4 个。
- 主要按预算档区分方案，再在方案内解释适合场景。
- 允许小幅超预算，但必须标红并说明原因；默认超出不超过 5%-10%。
- 方案卡片不强调数字总分，只展示推荐度、预算状态、完整度和风险标签。

方案调整状态：

- 用户可排除已有品类。已排除项保留在方案里，但不计入总价。
- 用户可锁定单品。后续调整不得自动替换锁定商品。
- 用户调整方案后生成新版本，默认展示最新版本，并保留查看修改记录的空间。
- 未锁定商品缺货或涨价时可以给替换建议，但不能无声替换；锁定商品必须先询问用户。

### Android 展示

导购入口先落地组合方案展示，不先新增独立方案中心。保存后的方案后续可进入“我的方案”恢复。

Android 展示分支：

- 只有 `products`：使用现有商品推荐列表和商品对比。
- 有 `bundle_plans`：使用方案卡片和方案对比。
- 方案详情内的单品继续跳转商品详情，或复用现有商品卡片的展开形态。

`BundlePlanCard` 是购买决策卡，不是大商品卡列表。默认结构：

- 方案标题：例如“方案二 · 6000 元均衡档”。
- 总价状态：例如“¥5,860 / ¥6,000”。
- 状态标签：基本配齐、风险 1 项、待确认 1 项、价格检查时间。
- 适合场景。
- 核心取舍。
- 关键商品清单，默认展示 4-5 个关键商品，其余折叠。
- 预算分配摘要。
- 与其他预算档差异。
- 操作：查看方案详情、替换单品、方案对比、保存方案、继续调整这套。

商品行默认展示“品类 + 商品名”，而不是只展示商品名。每行至少包含：

- 品类。
- 商品短标题。
- 价格。
- 一个推荐理由标签或角色。
- 可替换状态。
- 已排除或已锁定状态。

方案卡片顶部只展示搭配风险汇总，详情页展示完整兼容性检查。关键排除原因在卡片内最多展示 2 条，完整排除逻辑放详情页。

### 方案对比

当用户预期输出是商品组合时，使用方案对比；当用户预期输出是单个商品时，使用商品对比。

移动端方案对比优先使用并排摘要卡和分组对比项，不使用传统大表格作为主体验。方案对比字段：

- 总价。
- 预算状态。
- 完整度。
- 必选品类覆盖。
- 可选补充数量。
- 待确认项。
- 核心升级点。
- 主要风险。
- 适合场景。
- 可替换项数量。
- 售后/平台一致性。

整套电脑/办公桌面可增加：

- 性能余量。
- 显示体验。
- 外设体验。
- 升级空间。

开学好物可增加：

- 便携性。
- 宿舍适配。
- 学习效率。
- 耐用性。

### 第一版边界

第一版做：

- 识别组合需求。
- 返回 `bundle_plans`。
- 默认 3 个预算档方案。
- 方案卡片。
- 方案详情。
- 方案对比。
- 替换、排除、锁定的交互入口。
- 保存和恢复方案的基础数据结构。
- 价格和库存检查时间。
- 兼容性和搭配风险摘要。

第一版暂缓：

- 一键跨平台下单。
- 复杂预算手动编辑。
- 公开分享链接。
- 多人协作。
- 长期价格追踪。
- 自动重算所有历史方案。

### 演示数据策略

组合方案能力第一阶段只补充确定性 demo seed 数据，用于验证导购体验、方案卡片和方案对比，不改变 BuyWise 现有 AI 智能导购能力框架。

BuyWise 仍保留单品推荐、商品对比、价格/参数/口碑解释、多模态识别和已购反馈闭环。组合方案推荐只是新增的高级导购分支：用户问单个商品时继续走 `products` 和商品对比，用户要求配齐多品类商品时才走 `bundle_plans` 和方案对比。

新增商品数据不进入 closed beta 真实目录，不混入 `data/beta-catalog.csv`。closed beta 仍按真实商品 CSV、真实链接、真实图片和发布前导入校验执行；demo 组合数据继续通过 `app/scripts/demo_products.py` 或等价 seed profile 管理。

第一批 demo 组合场景只覆盖“桌面/电脑外设整套方案”，目标是支撑 3 个预算档和局部替换演示，而不是扩成完整垂类商城。建议最小数据规模：

- 电脑/主机：3 个。
- 显示器：3 个。
- 键盘：3 个。
- 鼠标：3 个。
- 耳机：3 个。
- 台灯、支架、拓展坞、插排：各 2 个。

这个规模约 23 个新增或可复用商品，足够展示入门、均衡、高配方案，覆盖总价、预算超出、完整度、兼容性风险、替换单品和方案对比。

## 影响

- `app/schemas/chat.py`：新增 `BundlePlan`、`BundlePlanItem`、`BundleCompleteness`、`BundleCompatibilityCheck` 等响应 schema，并在 `ChatResponse` 增加 `bundle_plans`。
- `app/services/intent_service.py` 与 `app/services/intent_llm.py`：将组合需求抽取为明确的 `bundle_recommend`，并输出模板品类和待确认项。
- `app/services/chat_service.py` 与 `app/services/chat_stream_service.py`：组合需求走方案生成和方案 payload；单品需求继续走现有 `products`。
- `app/services/recommend_service.py` 或新增 bundle service：按预算档、品类模板、完整度、兼容性和库存价格状态生成方案级结果。
- `tests/`：补充组合意图、方案响应、预算状态、超预算解释、缺口标注、锁定/排除状态和流式事件测试。
- `android-app/app/src/main/java/com/buywise/android/data/Models.kt`：新增 `BundlePlan` 相关强类型模型。
- `android-app/app/src/main/java/com/buywise/android/data/ApiDtos.kt` 与 mapper：解析 `bundle_plans`。
- `android-app/app/src/main/java/com/buywise/android/ui/screens/GuideScreen.kt`：根据 `bundle_plans` 渲染方案分支。
- Android UI components：新增 `BundlePlanCard`、方案商品行、方案对比摘要组件，并复用现有商品详情入口。
- `app/scripts/demo_products.py`：补充桌面/电脑外设整套方案所需的确定性 demo 商品；不得与 closed beta 真实目录混用。
- `docs/reference/api.md` 与 `docs/reference/frontend-support.md`：实现后同步组合推荐契约。

## 验证

- 后端 schema 测试覆盖 `ChatResponse.bundle_plans` 序列化和旧 `products` 兼容。
- 意图测试覆盖“一整套电脑”“开学好物”“已有显示器”“只买键盘”等分支。
- 服务测试覆盖默认 3 个预算档、5%-10% 超预算解释、必选/可选/需确认品类、已排除不计入总价、锁定商品不被替换。
- API 测试覆盖普通 chat 和 streaming chat 都能返回方案 payload。
- Demo seed 测试覆盖桌面/电脑外设所需品类和 3 个预算档可组装性。
- Android mapper 测试覆盖 `bundle_plans` 解析和旧响应兼容。
- Android UI 检查覆盖方案卡片默认展示 4-5 个关键商品、折叠可选项、预算超出标红、方案对比入口和单品详情跳转。
- 文档变更运行 `python scripts/validate_docs.py`。

## 最近检查

2026-06-05
