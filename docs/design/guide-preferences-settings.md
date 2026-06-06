# 设计：导购偏好与最小通用设置

Status: Implemented

## 背景

BuyWise 当前是 AI 购物决策助手，已经覆盖单品推荐、商品对比、识图导购、整套方案推荐等能力。随着组合方案能力加入，用户会更频繁表达长期稳定偏好，例如常用预算、是否允许小幅超预算、偏好静音或性价比、已有设备、排除品牌等。

这些偏好如果只在每次对话中临时表达，会增加用户重复输入成本；如果被 AI 隐式记住，又会造成不透明和不可控。因此第一版需要增加一组可见、可编辑、可撤销的“导购偏好”，用于提升推荐质量，而不是把产品改造成复杂用户画像系统或大而全设置中心。

本设计不改变 BuyWise 的产品定位：BuyWise 仍然是 AI 购物决策助手。桌面好物 / 电子产品是第一版导购偏好的重点演示垂类，不代表系统架构只能服务该品类。

## 目标

- 在账号页承载账号、导购偏好、数据与隐私、最小通用设置。
- 让导购偏好成为推荐上下文，直接影响预算、筛选、排序、排除、结果结构和解释深度。
- 支持单品推荐和整套方案推荐共用一份偏好字段，但在应用层按不同场景解释。
- 让用户知道本次推荐使用了哪些长期偏好，并可在本次任务中关闭。
- 支持未登录用户使用本地临时偏好，登录后再由用户确认是否合并到账号。

## 非目标

- 不新增独立设置 Tab。
- 不做复杂用户画像、广告画像或泛个人资料。
- 不自动把对话内容沉淀为长期偏好。
- 不做每条偏好的即时关闭；第一版只支持“本次不用全部偏好”。
- 不做多语言、通知细项、字体大小、首页布局自定义或大量实验开关。
- 不把 BuyWise 收窄成只服务整套方案或配电脑工具。

## 方案

### 信息架构

Android 底部导航不新增设置入口，保留账号入口，并升级为“账号与偏好”。账号页分组：

- 登录状态：手机号登录、退出登录。
- 导购偏好：预算策略、常用预算、核心偏好、排除项、已有设备、推荐呈现方式。
- 数据与隐私：偏好使用说明、清除导购偏好。
- 通用设置：清除本地缓存、主题跟随系统 / 浅色 / 深色（如果当前主题架构支持）。
- 反馈与关于。

导购页和结果页提供轻量入口：

- 导购页可以提示“使用我的导购偏好”。
- 结果页展示“已按你的导购偏好：静音优先、允许小幅超预算、已有显示器”。
- 结果页提供“本次不用偏好”和“编辑偏好”。

### 第一版字段

导购偏好以结构化字段为主，少量自由文本补充：

- `budget_policy`: `strict` / `slightly_flexible` / `quality_first`
- `single_item_budgets`: 按品类保存预算区间
- `bundle_budget_range`: 整套方案常用预算区间
- `priority_tags`: 性价比、静音、耐用、颜值、便携、游戏性能、办公效率、售后稳定
- `excluded_tags`: 不要二手、不要 RGB、不要无线、小众品牌谨慎等
- `excluded_brands`: 用户手动输入的排除品牌
- `owned_categories`: 已有键盘、鼠标、耳机、显示器、电脑、桌面配件等
- `presentation_style`: `direct_answer` / `compare_options` / `detailed_explanation`
- `extra_notes`: 补充说明，例如“宿舍空间小，桌面不能太乱”

第一版品类范围聚焦桌面好物 / 电子产品：

- 键盘
- 鼠标
- 耳机
- 显示器
- 电脑 / 主机 / 笔记本
- 桌面配件
- 开学 / 办公相关电子好物

预算偏好统一使用区间表达，超预算判断基于区间上限。第一版只做品类预算和整套方案预算，不做按场景预算矩阵。

### 后端 API

新增独立导购偏好 API，偏好管理不塞进 chat 接口：

- `GET /api/v1/guide/preferences`
- `PUT /api/v1/guide/preferences`
- `DELETE /api/v1/guide/preferences`

chat 接口负责使用偏好，不负责管理偏好。chat request 增加请求级控制：

- `ignore_saved_preferences: true | false`
- 可选临时偏好，用于未登录用户或本次任务覆盖

chat response 增加结构化 `applied_preferences`：

```json
{
  "applied_preferences": {
    "used_saved_preferences": true,
    "ignored_saved_preferences": false,
    "budget_policy": "slightly_flexible",
    "presentation_style": "compare_options",
    "summary": [
      "静音优先",
      "允许小幅超预算",
      "已有显示器"
    ],
    "constraints": [
      {
        "type": "owned_category",
        "key": "monitor",
        "label": "已有显示器",
        "effect": "整套方案不再把显示器作为必选项"
      }
    ]
  }
}
```

`constraints` 第一版只用于展示和测试，为未来单条关闭偏好保留结构空间。

### 数据模型

第一版采用一张账号级偏好表，核心字段列化，其余结构放 JSON，避免过早拆成多张表：

- `user_guide_preferences`
- `user_id`
- `budget_policy`
- `presentation_style`
- `preferences_json`
- `created_at`
- `updated_at`

`budget_policy` 和 `presentation_style` 是高频控制字段，单独列化；品类预算、整套预算、偏好标签、排除项、已有设备、补充说明放入 `preferences_json`。

### 偏好合并优先级

推荐上下文按以下优先级合并：

1. 本次对话显式输入
2. 本次请求临时偏好
3. 账号级导购偏好
4. 系统默认值

如果 `ignore_saved_preferences = true`，后端跳过账号级导购偏好，仅使用本次输入、临时偏好和系统默认值。该开关只影响当前对话或当前推荐任务，不修改长期偏好。

后端需要先把偏好转换成确定性约束，再交给推荐服务和组合方案服务执行。LLM 只负责表达增强和少量语义解释，不负责核心预算、排除和已有设备规则。

### 推荐应用规则

预算策略：

- `strict`: 默认不超预算；如果预算内可选少，明确说明限制。
- `slightly_flexible`: 允许超过预算上限 5%-10%，必须标红并说明原因。
- `quality_first`: 可以推荐更高档方案，但必须说明超出常用预算换来了什么。

单品推荐：

- 常用单品预算作为默认预算来源，本次预算永远优先。
- `priority_tags` 影响商品排序和对比维度。
- `excluded_tags`、`excluded_brands` 参与筛选或降权。
- `presentation_style = compare_options` 时展示商品对比。

整套方案推荐：

- 常用整套预算作为默认预算来源，本次预算永远优先。
- `owned_categories` 从必选清单中移除，或进入可选升级项。
- 预算策略影响入门 / 均衡 / 进阶方案的档位和超预算阈值。
- `presentation_style = compare_options` 时展示方案对比。
- 超预算方案必须在价格和说明中明确标记。

### 未登录与合并

未登录用户可以设置本地临时导购偏好，用于当前设备上的导购请求。UI 需要提示“登录后可同步导购偏好”。

登录后不自动合并本地偏好到账号。冲突处理：

- 账号已有 `budget_policy` 或 `presentation_style` 时，默认保留账号值。
- 本地新增的 `priority_tags`、`excluded_tags`、`owned_categories` 可勾选合并。
- `excluded_brands` 可去重合并，但仍需确认。
- `extra_notes` 不自动拼接。
- 账号偏好为空时，可以提示“一键同步到账号”。

### AI 偏好沉淀

第一版不自动保存从对话中推断出的长期偏好。AI 只能做弱提醒：

“你经常提到低噪和桌面收纳，要加入导购偏好吗？”

用户确认后才写入账号级导购偏好。所有长期偏好必须可查看、可编辑、可删除、可重置。

## 影响

后续实现会影响：

- Backend schemas: guide preference request / response、chat request、chat response
- Backend routes: `app/api/v1/` 下新增导购偏好路由并注册到 API router
- Backend services: chat preference merge、recommend service、bundle recommend service
- Backend repositories and models: `user_guide_preferences`
- Android data layer: guide preference models、repository、local cache
- Android UI: 账号与偏好页、导购页偏好提示、结果页已应用偏好提示
- Docs: API reference、frontend support、system overview、implementation deep dive
- Tests: schema tests、API tests、chat merge tests、recommend / bundle behavior tests、Android parsing and rendering checks

## 验证

实现完成后至少验证：

- `GET / PUT / DELETE /api/v1/guide/preferences` 行为正确。
- chat 在默认情况下合并账号偏好。
- `ignore_saved_preferences = true` 时 chat 不使用账号偏好。
- 本次输入覆盖账号偏好。
- `applied_preferences` 结构化返回，Android 能稳定展示摘要。
- `strict`、`slightly_flexible`、`quality_first` 三种预算策略影响推荐和方案预算。
- `owned_categories` 会影响整套方案必选清单。
- 单品请求仍返回商品对比，组合请求仍返回方案对比。
- 未登录本地偏好不自动写入账号。
- 清除导购偏好后推荐回到系统默认行为。
- 文档校验通过。

## 最近检查

2026-06-06
