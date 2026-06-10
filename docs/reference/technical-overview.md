# 技术总览

本文档用于项目展示、技术评审和工程交接，概括 BuyWise 的系统架构、技术栈、依赖环境、目录结构、配置说明和关键问题解决方案。更细的边界、接口、配置和脚本说明分别维护在 `docs/architecture/` 与 `docs/reference/` 下。

## 项目定位

BuyWise 是一个多模态电商导购系统，仓库包含三个主要交付面：

- FastAPI 后端：提供商品、对比、聊天、RAG、上传、视觉、语音、订单、反馈和后台维护 API。
- 原生 Android 客户端：Kotlin Jetpack Compose 应用，通过 JSON 和 SSE 接口完成导购、商品展示、组合方案、购物车和反馈闭环。
- 后台管理端：React/Vite/TypeScript 单页应用，随后端镜像构建并作为内部管理入口使用。

核心业务链路为：用户在 Android 输入文字、图片或语音需求，后端抽取结构化购物意图，结合偏好和商品索引检索候选商品，调用推荐、组合方案或对比服务，再通过 LLM 生成导购回复，并以 SSE 或 JSON 形式返回客户端。

## 系统架构

BuyWise 后端采用分层架构，依赖方向保持从入口到基础设施单向流动：

```text
Android / Admin Web / API Client
            |
            v
FastAPI app.main + app.api.router
            |
            v
app.api.v1 routes
            |
            v
app.services business flow
            |
            +--> app.repositories + SQLAlchemy models + MySQL
            +--> app.ai + provider clients
            +--> app.vectorstore + ChromaDB
            +--> upload storage: local or Tencent COS
            +--> app.core.providers for auth, logging, telemetry, errors
```

主要边界：

- API 层只负责 HTTP 契约、依赖注入和错误映射，业务流程下沉到 `app/services/`。
- Service 层编排 repository、RAG、AI provider、上传和订单反馈逻辑。
- Repository 层只处理 SQLAlchemy session 上的数据访问。
- 横切能力必须通过 `app.core.providers` 访问，包括认证、日志、错误处理和 telemetry。
- Android 端以 repository + ViewModel 管理远程调用与界面状态，不直接耦合后端内部实现。

当前端到端导购链路为：

```text
Android 输入需求
  -> /api/v1/ai/chat/stream
  -> 意图抽取和偏好合并
  -> 商品检索和 RAG rerank
  -> 推荐排序、对比或组合方案生成
  -> LLM 回复生成
  -> SSE 分块返回
  -> Android 展示消息、商品卡片、组合方案和偏好摘要
```

非流式 `/api/v1/ai/chat` 保留给测试、兼容和调试。

## 技术栈

后端运行栈：

- Python 3.11。
- FastAPI `0.136.1`，Uvicorn `0.46.0`。
- SQLAlchemy `2.0.49`，Alembic `1.18.4`，PyMySQL `1.1.3`。
- Pydantic `2.13.4` 与 pydantic-settings `2.14.1`。
- MySQL 8.0 作为主数据库。
- ChromaDB `1.5.9` 作为本地持久化向量索引。
- OpenAI SDK `2.36.0` 连接 OpenAI-compatible LLM、embedding 和视觉模型。
- Tencent Cloud SDK 与 COS SDK 用于腾讯 ASR 和对象存储。
- prometheus-fastapi-instrumentator 用于 HTTP 和业务指标暴露。

Android 客户端：

- Kotlin + Android Gradle Plugin。
- Jetpack Compose，Compose BOM `2026.03.00`。
- compileSdk/targetSdk 36，minSdk 26。
- Java/Kotlin JVM target 17。
- OkHttp `4.12.0` 与 OkHttp SSE 对接流式聊天。
- kotlinx-serialization-json `1.9.0` 处理接口契约。
- Coil 3 加载商品图片。
- Navigation Compose 和 Lifecycle ViewModel Compose 管理页面流转与状态。

后台管理端：

- React `19.2.0`。
- TypeScript `5.9.3`。
- Vite `7.2.0`。
- react-router-dom `7.9.6`。
- Docker 镜像构建阶段使用 Node 24 Alpine 生成 `admin-web/dist`，再复制到 Python 后端镜像。

## 依赖环境

本地后端开发建议使用仓库内虚拟环境：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Docker Compose 默认启动后端和 MySQL：

```powershell
docker compose up --build
```

Compose 运行时约定：

- 后端容器暴露 `8000`，宿主机端口可通过 `BACKEND_PORT` 覆盖。
- MySQL 使用 `mysql:8.0`，宿主机端口可通过 `MYSQL_PORT` 覆盖。
- `data/`、`vector_store/` 和 `uploads/` 会挂载进容器，分别保存数据文件、Chroma 索引和本地上传文件。
- Dockerfile 会先构建 `admin-web`，再构建 Python 后端镜像。

Android 构建环境：

- 需要 Android SDK 36 和 Java 17。
- `ANDROID_API_BASE_URL` 默认是 `http://10.0.2.2:8000`，用于模拟器访问宿主机后端。
- release 构建需要配置 `ANDROID_RELEASE_KEYSTORE_FILE`、`ANDROID_RELEASE_KEYSTORE_PASSWORD`、`ANDROID_RELEASE_KEY_ALIAS` 和 `ANDROID_RELEASE_KEY_PASSWORD`。

后台管理端构建：

```powershell
cd admin-web
npm run build
```

## 目录结构

仓库关键目录职责如下：

- `app/`：FastAPI 后端主体。
- `app/api/v1/`：版本化 HTTP 路由。
- `app/services/`：业务流程和用例编排。
- `app/repositories/`：数据库访问层。
- `app/models/`：SQLAlchemy 数据模型。
- `app/schemas/`：Pydantic 请求和响应契约。
- `app/ai/`：LLM、embedding、视觉和 RAG 相关客户端与流程。
- `app/vectorstore/`：ChromaDB 商品索引访问。
- `app/core/`：配置、依赖、provider、错误、日志和 telemetry。
- `android-app/`：原生 Android 客户端。
- `admin-web/`：后台管理端 React/Vite 应用。
- `alembic/`：数据库迁移。
- `data/`：商品 CSV、评测集和本地数据模板。
- `docs/`：项目架构、设计、约定、参考和运维文档。
- `scripts/`：验证、发布、演示、导入、索引、smoke 和维护脚本。
- `observability/`：Prometheus、Loki、Promtail 和 Grafana 配置。
- `vector_store/`：本地 Chroma 持久化目录。
- `uploads/`：本地上传文件目录。

## 配置说明

环境变量示例文件位于 `.env.dev.example`、`.env.test.example` 和 `.env.prod.example`。完整配置清单见 `docs/reference/configuration.md`。

主要配置域：

- 应用基础配置：`APP_NAME`、`APP_ENV`、`APP_PORT`、`APP_DEBUG`、`API_V1_PREFIX` 和 `LOG_LEVEL`。
- 数据库配置：`MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE` 和 `SQLALCHEMY_ECHO`。
- AI 配置：`LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`EMBEDDING_PROVIDER`、`VISION_PROVIDER` 和 `SPEECH_PROVIDER`。
- 向量索引配置：`CHROMA_PERSIST_DIR` 和 `CHROMA_PRODUCT_COLLECTION`。
- 上传配置：`UPLOAD_PROVIDER`、`UPLOAD_DIR`、`UPLOAD_PUBLIC_BASE_URL`、`UPLOAD_MAX_BYTES`、`UPLOAD_ALLOWED_TYPES`、`COS_BUCKET` 和 `COS_REGION`。
- 安全配置：`AUTH_API_KEYS`、`READINESS_TOKEN`、`ADMIN_JWT_SECRET`、`USER_JWT_SECRET` 和 OTP 限流相关变量。
- 流式聊天与限流配置：`CHAT_STREAM_HEARTBEAT_SECONDS`、`CHAT_STREAM_MAX_SECONDS`、`CHAT_RATE_LIMIT_PER_MINUTE`、`VISION_RATE_LIMIT_PER_MINUTE`、`SPEECH_RATE_LIMIT_PER_MINUTE` 和 `UPLOAD_RATE_LIMIT_PER_MINUTE`。
- Android 构建配置：`ANDROID_API_BASE_URL`、`BUYWISE_BETA_TOKEN`、`BUYWISE_UPLOAD_TOKEN` 和 `BUYWISE_SHOW_DEBUG_INFO`。

生产环境约束：

- `APP_ENV=prod` 时必须关闭 debug，并配置非占位密钥、readiness token、JWT secret、MySQL 密码和显式 CORS origin。
- `ALLOW_MOCK_PROVIDERS_IN_PROD=false` 时，LLM、embedding 和 vision provider 不能使用 mock；closed beta 阶段允许 `SPEECH_PROVIDER=mock`。
- 非 mock 视觉或语音 provider 需要公网可访问上传 URL，可通过 `UPLOAD_PUBLIC_BASE_URL` 或 `UPLOAD_PROVIDER=cos` 满足。
- Android beta token 应来自后端 `AUTH_API_KEYS`，并具备需要的 upload、orders 和 feedback scope；不要把 readiness token 放进 Android 包。

## 关键问题解决方案

AI provider 不稳定或返回非 JSON：

- LLM 意图抽取失败时，后端回退到规则抽取，保证基础导购链路可用。
- provider 并发由 `AI_LLM_MAX_CONCURRENCY`、`AI_VISION_MAX_CONCURRENCY` 和 `AI_SPEECH_MAX_CONCURRENCY` 控制。
- provider 超时由 `AI_PROVIDER_TIMEOUT_SECONDS` 控制，容量不足时通过 `Retry-After` 暴露重试建议。

RAG 索引缺失或陈旧：

- 商品导入和 seed 不会自动重建索引，发布或演示前需要显式运行索引构建。
- 使用 `python -m app.scripts.build_vector_index --mode rebuild` 重建索引。
- 使用 `python -m app.scripts.check_vector_index` 检查商品、collection 和内容哈希一致性。
- 发版质量门禁可通过 `python -m app.scripts.rag_eval_gate` 验证召回和排序质量。

上传文件无法被外部视觉或语音 provider 访问：

- 本地相对路径只适合 mock 或本地演示。
- 真实 provider 需要 `UPLOAD_PUBLIC_BASE_URL` 拼接公网 URL，或使用 COS 返回公网对象 URL。
- `UPLOAD_MAX_BYTES` 限制单文件大小，`REQUEST_MAX_BYTES` 限制入口请求体大小。

closed beta 身份和权限：

- closed beta 使用受控 API key，不等同于完整公网账号系统。
- `AUTH_API_KEYS` 采用 `subject:token:scope1,scope2` 格式。
- prod 下订单、反馈和上传接口必须携带满足 scope 的 Bearer token。
- readiness token 单独保护 `/api/v1/ready`，不得复用普通用户或 beta API key。

SSE 流式聊天超时和首屏体验：

- `/api/v1/ai/chat/stream` 使用 heartbeat 保持连接活性。
- `CHAT_STREAM_MAX_SECONDS` 限制单次流式响应最长持续时间，超时后返回 `chat_stream_timeout`。
- 文本导购可启用 fast products 路径，在简单品类需求下先返回候选商品，再生成短回复。

后台维护任务重复执行：

- 上传清理、索引检查、备份检查和 release prepare 均通过脚本和外部调度执行。
- FastAPI 进程内不引入常驻 scheduler，避免多副本部署时重复执行维护任务。

中文文档和数据乱码：

- 文档和文本文件统一使用 UTF-8。
- PowerShell 脚本入口会加载 `scripts/set_utf8.ps1`。
- 如果终端查看中文 seed 或 CSV 出现乱码，先执行 `. .\scripts\set_utf8.ps1`。

## 验证与运维入口

提交前常用验证：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

文档变更验证：

```powershell
python scripts\validate_docs.py
```

closed beta 发布前准备示例：

```powershell
.\scripts\release_prepare.ps1 -ImportCsv .\data\beta-catalog.csv -RequireRealCatalog -BuildIndex -IndexMode rebuild -CheckIndex
```

发布后 smoke 示例：

```powershell
.\scripts\closed_beta_verify.ps1 -ExpectedActiveProducts 50 -IncludeAi
```

更多运行、观测和脚本说明见：

- `docs/architecture/runtime-observability.md`
- `docs/reference/scripts.md`
- `docs/reference/configuration.md`
- `docs/reference/api.md`
