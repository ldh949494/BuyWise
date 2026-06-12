# BuyWise

BuyWise 是一个多模态电商导购 Agent 项目，面向“描述需求 -> 理解意图 -> 检索商品 -> 生成推荐 -> 购买与反馈”的闭环体验。

仓库包含 FastAPI 后端、原生 Android 客户端和 React/Vite 后台管理端。当前重点是可运行的文本导购 MVP，并保留图片识别、语音识别、上传、向量检索和 OpenAI-compatible LLM 接入能力。

Agent 工作说明见 [AGENTS.md](AGENTS.md)。更完整的架构、约定、配置和脚本说明维护在 [docs/](docs/)。

## 项目速览

| 交付面 | 技术栈 | 主要职责 |
| --- | --- | --- |
| 后端 API | FastAPI, SQLAlchemy, Alembic, MySQL, ChromaDB | 商品、对比、导购、RAG、上传、视觉、语音、订单、反馈和后台维护 API |
| Android 客户端 | Kotlin, Jetpack Compose, OkHttp SSE | 导购对话、商品卡片、组合方案、追问、识图、购物车和反馈闭环 |
| 后台管理端 | React, TypeScript, Vite | 内部商品维护、图片上传和运行摘要查看 |
| 运维与验证 | Docker Compose, PowerShell, pytest, Playwright | 本地开发、隔离 PR 环境、closed beta 验证和浏览器 smoke |

核心链路：

```text
Android / Admin Web / API Client
  -> FastAPI /api/v1
  -> app.services
  -> repositories + MySQL
  -> app.ai + ChromaDB + upload storage
  -> JSON / SSE response
```

## 快速开始

### 1. 准备环境

- Python 3.11
- Docker Desktop，用于本地 MySQL 或完整 Compose 环境
- Android Studio 与 Android SDK 36，用于 Android 客户端
- Node.js 与 npm，用于单独开发后台管理端

如果仓库内还没有虚拟环境：

```powershell
py -3.11 -m venv .venv
```

安装后端依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

复制本地配置：

```powershell
Copy-Item .env.example .env
```

### 2. 启动后端

先启动 MySQL：

```powershell
docker compose up -d mysql
```

再启动本机开发后端：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
```

`start_backend.ps1` 会设置 UTF-8、执行数据库迁移并启动 Uvicorn。如果 `.env` 里是 `MYSQL_HOST=mysql`，脚本会在本机进程内改用 `127.0.0.1` 连接 Docker 暴露的 MySQL。

常用入口：

| 入口 | URL |
| --- | --- |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| Health | `http://127.0.0.1:8000/api/v1/health` |
| Readiness | `http://127.0.0.1:8000/api/v1/ready` |
| Admin Web | `http://127.0.0.1:8000/admin`，需要先构建 `admin-web/dist` |

也可以直接运行 Uvicorn，但需要确保 `.env` 中的 `MYSQL_HOST` 能被本机解析：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 3. 准备演示数据

本地演示优先使用确定性 demo seed，便于固定推荐命中和商品卡片展示：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_demo.ps1
```

未配置真实 LLM key 时，可以做离线 smoke：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_demo.ps1 -AllowMockLlm
```

手动准备数据时依次运行：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_database
.\.venv\Scripts\python.exe -m app.scripts.seed_products --profile demo
.\.venv\Scripts\python.exe -m app.scripts.build_vector_index
```

如果使用真实商品 CSV：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.import_products
.\.venv\Scripts\python.exe -m app.scripts.migrate_product_images_to_cos --apply
.\.venv\Scripts\python.exe -m app.scripts.build_vector_index
```

`import_products` 默认读取本地忽略文件 `data/beta-catalog.csv`，并按 `sku` upsert。真实图片应先写成可公网访问 URL，再用 COS 迁移脚本固化为稳定资源。

推荐演示问题：

```text
帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高
```

后端启动后可检查演示 API：

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_api_check.py --base-url http://127.0.0.1:8000
```

### 4. 启动 Android 客户端

使用 Android Studio 打开 [android-app/](android-app/)。

构建 Debug 包：

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

后端地址约定：

| 运行方式 | API Base URL |
| --- | --- |
| Android 模拟器访问宿主机后端 | `http://10.0.2.2:8000` |
| 真机访问电脑上的后端 | `http://<电脑局域网 IP>:8000` |

Android 端通过 `/api/v1/ai/guide/stream` 开始或刷新完整导购，通过 `/api/v1/ai/guide/follow-up/stream` 基于当前推荐快照处理追问。

### 5. 启动后台管理端

后台管理端可以单独用 Vite 开发，接口会代理到本机后端：

```powershell
cd admin-web
npm install
npm run dev
```

默认地址是 `http://127.0.0.1:5173/admin/`。生产或 Docker 镜像中，构建产物会挂载到后端 `/admin`。

构建后台管理端：

```powershell
cd admin-web
npm run build
```

dev/test 下，如果数据库中还没有 `admin` 用户，可以使用内置账号 `admin` / `buywise-admin` 登录后台。生产环境禁用内置账号，管理员账号通过脚本创建：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.create_admin_user --username admin --password <password>
```

## Docker

完整 Compose 模式启动后端和 MySQL：

```powershell
docker compose up --build
```

容器启动后执行迁移、导入和索引构建：

```powershell
docker compose exec backend python -m app.scripts.migrate_database
docker compose exec backend python -m app.scripts.import_products
docker compose exec backend python -m app.scripts.migrate_product_images_to_cos --apply
docker compose exec backend python -m app.scripts.build_vector_index
```

Compose 网络内 `MYSQL_HOST=mysql` 是正确配置。closed beta 生产模式使用 `docker-compose.prod.yml`、COS、HTTPS 反代、readiness 和 smoke 验证，流程见 [closed-beta-runbook.md](docs/operations/closed-beta-runbook.md)。

## 常用命令

| 目标 | 命令 |
| --- | --- |
| 快速验证后端和文档 | `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild -SkipAdminWebBuild` |
| 包含后台前端构建的验证 | `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild` |
| 包含 Android 构建的一键验证 | `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall` |
| 仅校验文档 | `python scripts\validate_docs.py` |
| 仅校验 provider 边界 | `python scripts\validate_providers.py` |
| 仅校验仓库 lint | `python scripts\validate_repo_lint.py` |
| 仅校验熵债 | `python scripts\validate_entropy.py` |
| 重建向量索引 | `.\.venv\Scripts\python.exe -m app.scripts.build_vector_index --mode rebuild` |
| 只更新一个商品索引 | `.\.venv\Scripts\python.exe -m app.scripts.build_vector_index --mode upsert --product-id 123` |

本机临时目录权限异常时，可以把 pytest 临时目录切到仓库内：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_tmp\manual
```

## 浏览器检查

安装 Playwright Chromium：

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

检查本地 API 和文档页：

```powershell
.\.venv\Scripts\python.exe .\scripts\browser_check.py --base-url http://127.0.0.1:8000 --record-video
```

使用已有 Chrome CDP：

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir=.chrome-agent
.\.venv\Scripts\python.exe .\scripts\browser_check.py --base-url http://127.0.0.1:8000 --cdp-url http://127.0.0.1:9222
```

## PR 环境

启动隔离 PR 环境：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -Branch feature/pr-123 -BackendPort 8123 -MysqlPort 3323
```

停止环境：

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123
```

删除 volume 和 worktree：

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123 -RemoveVolumes -RemoveWorktree
```

带观测组件启动：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

默认入口：

| 服务 | URL |
| --- | --- |
| Backend | `http://127.0.0.1:8123` |
| Prometheus | `http://127.0.0.1:9090` |
| Loki | `http://127.0.0.1:3100` |
| Grafana | `http://127.0.0.1:3000`，默认账号 `admin` / `admin` |

## 项目结构

```text
app/
  ai/             LLM、embedding、视觉、语音、RAG 和 Agent 相关代码
  api/v1/         FastAPI v1 路由
  core/           配置、数据库、日志、错误和 provider
  integrations/   外部服务集成
  models/         SQLAlchemy ORM 模型
  repositories/   数据访问层
  schemas/        Pydantic API 契约
  services/       业务编排和用例逻辑
  scripts/        应用级脚本
  utils/          通用工具
  vectorstore/    ChromaDB 商品索引封装
admin-web/        React/Vite 后台管理端
android-app/      Kotlin Jetpack Compose 客户端
alembic/          数据库迁移
data/             Demo CSV、beta catalog 模板和本地数据
docs/             架构、约定、计划、产品和参考文档
observability/    Prometheus、Loki、Promtail、Grafana 配置
scripts/          仓库维护、验证、演示和发布脚本
tests/            后端测试
```

## API 入口

所有公开 API 默认挂载在 `/api/v1` 下。完整接口以 Swagger UI 和 [API 参考](docs/reference/api.md) 为准，常用入口如下：

| 能力 | 代表接口 |
| --- | --- |
| 健康检查 | `GET /api/v1/health`, `GET /api/v1/ready` |
| 用户认证 | `POST /api/v1/auth/otp/request`, `POST /api/v1/auth/otp/verify`, `GET /api/v1/auth/me` |
| 商品与对比 | `GET /api/v1/products`, `POST /api/v1/products/compare` |
| 导购与追问 | `POST /api/v1/ai/chat`, `POST /api/v1/ai/chat/stream`, `POST /api/v1/ai/guide/stream`, `POST /api/v1/ai/guide/follow-up/stream` |
| 检索与多模态 | `POST /api/v1/rag/search`, `POST /api/v1/upload`, `POST /api/v1/vision/recognize`, `POST /api/v1/visual-search`, `POST /api/v1/speech/asr` |
| 购物车和订单 | `POST /api/v1/cart/items`, `GET /api/v1/orders`, `POST /api/v1/orders` |
| 反馈与评价 | `GET /api/v1/feedback/prompts`, `POST /api/v1/reviews/from-order-item` |
| 后台管理 | `POST /api/v1/admin/auth/login`, `GET /api/v1/admin/products`, `GET /api/v1/admin/ops/summary` |

## 文档导航

| 主题 | 文档 |
| --- | --- |
| 系统概览 | [docs/architecture/system-overview.md](docs/architecture/system-overview.md) |
| 后端边界 | [docs/architecture/backend-boundaries.md](docs/architecture/backend-boundaries.md) |
| Android 边界 | [docs/architecture/android-boundaries.md](docs/architecture/android-boundaries.md) |
| 运行和观测 | [docs/architecture/runtime-observability.md](docs/architecture/runtime-observability.md) |
| 产品规格 | [docs/product/buywise-mvp.md](docs/product/buywise-mvp.md) |
| 技术总览 | [docs/reference/technical-overview.md](docs/reference/technical-overview.md) |
| API 参考 | [docs/reference/api.md](docs/reference/api.md) |
| 配置参考 | [docs/reference/configuration.md](docs/reference/configuration.md) |
| 脚本参考 | [docs/reference/scripts.md](docs/reference/scripts.md) |
| 数据源标准 | [docs/reference/catalog-data-source.md](docs/reference/catalog-data-source.md) |
| Closed beta 运维 | [docs/operations/closed-beta-runbook.md](docs/operations/closed-beta-runbook.md) |

## 开发约定

- 新后端路由放在 `app/api/v1/`，并在 `app/api/router.py` 注册。
- 业务逻辑放在 `app/services/`。
- 数据访问放在 `app/repositories/`。
- ORM 模型放在 `app/models/`。
- Pydantic schema 放在 `app/schemas/`。
- 测试放在 `tests/test_*.py`。
- Android 代码放在 `android-app/app/src/main/java/com/buywise/android/`。
- 认证、telemetry、日志和错误处理通过 `app.core.providers` 访问。

更多约定见 [docs/conventions/](docs/conventions/)。
