# 后端边界

后端是 FastAPI 应用，入口在 `app/main.py`。公共 API 默认挂载在 `/api/v1` 下。

## 分层

- `app/api/v1/`：路由层，只负责 HTTP 契约、依赖注入和状态码。
- `app/services/`：业务用例和编排，例如聊天、推荐、对比、上传、语音和视觉流程。
- `app/repositories/`：数据库查询和持久化辅助。
- `app/models/`：SQLAlchemy ORM 模型。
- `app/schemas/`：Pydantic 请求和响应模型。
- `app/ai/`：LLM、embedding、RAG prompt 和 agent 相关封装。
- `app/vectorstore/`：ChromaDB 商品向量索引封装。
- `app/integrations/`：外部服务客户端，例如 COS、视觉模型、语音识别。
- `app/core/`：配置、数据库、provider、日志、错误和请求上下文。

## 依赖方向

路由调用服务；服务组合 repository、AI、vector store 和 integrations；repository 只依赖模型和数据库 session。低层模块不得反向导入 API 路由。

## 事务边界

Repository 可以查询、`add`、`flush`、`refresh`，但不负责 `commit()` 或 `rollback()`。服务和脚本入口负责完整用例的事务提交与回滚。

## 横切能力

认证、日志、遥测、错误处理和请求上下文必须通过 `app.core.providers` 访问。变更这些能力后运行 `python scripts/validate_providers.py`。

## 稳定性

新增后端能力时优先放进已有层级。只有当现有边界无法表达职责时才新增包，并同步更新本文档。
