# 文件大小

源码文件应保持在 500 行以内。

## 修复模式

- 将 route 编排移动到 service。
- 将持久化代码移动到 repository。
- 将纯 helper 移动到 `app/utils/`。
- 将大型 Android 页面拆分为 `ui/components/` 或更小的 screen 文件。
- 测试保持聚焦；重复 fixture 或 builder 应抽取复用。

自定义仓库 linter 会报告超大文件，并给出直接修复建议。
