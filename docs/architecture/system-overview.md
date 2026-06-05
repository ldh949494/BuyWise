# 系统概览

BuyWise 是一个多模态电商导购项目，仓库包含 FastAPI 后端和原生 Android 客户端。

## 主要组件

- 后端 API：`app/main.py` 创建 FastAPI 应用，并挂载 `app/api/router.py` 中的版本化路由。
- API 层：`app/api/v1/` 暴露健康检查、商品、对比、聊天、RAG、上传、视觉和语音接口。
- 服务层：`app/services/` 负责业务流程，组合 repository、AI 客户端和外部集成。
- Repository 层：`app/repositories/` 负责 SQLAlchemy session 上的数据库访问。
- 数据模型层：`app/models/` 定义 SQLAlchemy 模型，`app/schemas/` 定义 Pydantic 契约。
- AI 和检索：`app/ai/` 与 `app/vectorstore/` 提供 LLM、embedding、RAG 和持久化 ChromaDB 商品索引。
- Android 客户端：`android-app/` 是 Kotlin Jetpack Compose 应用，使用 MVVM 风格状态管理，并通过 OkHttp repository 对接后端合同流。

更详细的架构设计和代码实现说明见 `docs/architecture/implementation-deep-dive.md`。

## 当前端到端链路

AI 导购链路为：Android 输入需求 -> `/api/v1/ai/chat/stream` -> 后端抽取结构化需求 -> RAG 检索商品 -> 推荐排序或组合方案生成 -> LLM 生成回复 -> SSE 分块返回 -> Android 展示回复、商品卡片或组合方案卡片。

非流式 JSON 聊天接口 `/api/v1/ai/chat` 仍保留，用于测试、兼容和调试。

## 依赖方向

路由依赖服务；服务依赖 repository、integration、AI 和 vector 组件；repository 依赖模型和数据库 session。低层模块不得导入 API 路由模块。

## 稳定性

本文档描述稳定模块边界。包结构移动、引入新层级或重大职责变化时必须同步更新。
