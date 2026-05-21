# 导入边界

分层导入可以避免实现细节在代码库中泄漏。

## 后端规则

- API 模块调用 service，并使用 schema/core dependency。
- Service 编排 repository、integration、AI、vector store、schema 和 utility。
- Repository 使用 model 和 core database helper。
- Model 不导入 API、service 或 repository 模块。
- Schema 可以导入共享 schema，但不得导入 service、repository、model 或 API 模块。

## 修复模式

当 lint 报告某层导入了禁止层时，把依赖移动到最近的允许 owner 后面。例如 API route 导入 repository 时，应创建或扩展 service 方法，并在 route 中注入该 service。
