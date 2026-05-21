# 后端约定

## API 路由

- 新路由放在 `app/api/v1/`，并在 `app/api/router.py` 注册。
- 路由函数保持轻量，只处理 HTTP 契约、依赖注入和响应模型。
- 业务逻辑放到 service，不在路由中直接写复杂流程。
- 使用依赖注入获取 service 和数据库 session。

## 服务与 Repository

- 业务逻辑和编排放在 `app/services/`。
- 持久化查询放在 `app/repositories/`。
- 除非端点刻意保持极小，否则不要在 route handler 中直接写 SQLAlchemy 查询。
- Repository 不拥有事务边界：可以 query、`add`、`flush`、`refresh`，但不得调用 `commit()` 或 `rollback()`。
- 服务和用例拥有事务边界。执行写操作的服务必须在完整用例成功后提交，失败时回滚。
- 数据维护脚本可以提交自己的 session，因为脚本是命令入口，不是 repository 代码。

## 异步边界

- `app/services/` 和 `app/ai/` 不直接导入 FastAPI 或 Starlette 运行时辅助。
- 异步流程中需要隔离阻塞 DB、vector store、embedding 或文件 I/O 时，使用 `app.core.concurrency.run_blocking_io`。

## Schema 与模型

- Pydantic 请求和响应契约放在 `app/schemas/`。
- SQLAlchemy 模型放在 `app/models/`。
- 数据库 schema 变更放在 `alembic/versions/`。
- 迁移从 `app.core.database.Base.metadata` 生成，提交前人工检查生成操作。
- API 响应形状变化必须有测试覆盖。

## 配置

- 环境变量配置放在 `app/core/config.py`。
- 新增公开环境变量时，同步更新 `.env.*.example` 和 `docs/reference/configuration.md`。

## 横切能力

- 认证、遥测、日志和错误处理通过 `app.core.providers` 访问。
- 功能模块不得直接导入日志、遥测、认证 session helper 或异常处理实现。
- 变更 provider 相关能力后运行 `python scripts/validate_providers.py`。
