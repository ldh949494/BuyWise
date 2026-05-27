# Closed Beta Catalog Taxonomy

Use this taxonomy when filling the closed beta product CSV. The goal is predictable retrieval and recommendation behavior, not exhaustive merchandising coverage.

## Categories

Stage 1 uses exactly these categories:

- `机械键盘`
- `蓝牙耳机`
- `台灯`
- `充电宝`
- `双肩包`

Use 10 real SKUs per category for the first beta catalog.

## Tags

Choose 4-8 tags per product. Tags describe product attributes, constraints, or differentiators.

### Shared

- `性价比`
- `轻便`
- `耐用`
- `高颜值`
- `送礼`
- `学生党`
- `办公`
- `便携`

### 机械键盘

- `低噪音`
- `无线`
- `三模`
- `蓝牙`
- `热插拔`
- `紧凑布局`
- `写代码`
- `长续航`

### 蓝牙耳机

- `降噪`
- `通话清晰`
- `低延迟`
- `长续航`
- `佩戴舒适`
- `运动`
- `通勤`
- `入耳式`

### 台灯

- `护眼`
- `无频闪`
- `高显色`
- `无级调光`
- `小巧`
- `阅读`
- `备考`
- `宿舍`

### 充电宝

- `快充`
- `USB-C`
- `轻薄`
- `大容量`
- `小容量`
- `自带线`
- `旅行`
- `应急`

### 双肩包

- `电脑仓`
- `防泼水`
- `大容量`
- `轻量`
- `通勤`
- `上课`
- `分区收纳`
- `简约`

## Suitable Scenes

Choose 2-5 scenes per product. Scenes describe where or why the user would use the product.

- `宿舍`
- `通勤`
- `办公`
- `学习`
- `写代码`
- `阅读`
- `旅行`
- `送礼`
- `应急`
- `备考`
- `上课`
- `运动`

## Writing Rules

- Prefer existing terms from this file instead of inventing synonyms.
- Do not mix near-duplicates such as `宿舍`, `寝室`, and `学生宿舍`; use `宿舍`.
- Do not put prices, stock, platform names, or model numbers in `tags`.
- Keep product-specific details in `description`, `specs`, and `review_summary`.
- `tags` and `suitable_scene` must be JSON arrays in the CSV.
