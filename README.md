# BuyWise

Agent instructions start at `AGENTS.md`.

BuyWise 是一个多模态电商导购 Agent 项目，包含 FastAPI 后端和原生 Android 客户端。当前里程碑是可运行的文本导购 MVP，并预留图片识别、语音识别、上传、向量检索和 LLM 接入能力。

## 快速开始

### 后端

1. 准备 Python 3.11 环境。
2. 安装依赖：

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. 复制环境变量模板：

   ```powershell
   Copy-Item .env.example .env
   ```

4. 启动 API：

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
   ```

5. 打开接口文档和健康检查：
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - Health: `http://127.0.0.1:8000/api/v1/health`

### Demo 数据

运行迁移、导入商品数据并构建向量索引：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.migrate_database
.\.venv\Scripts\python.exe -m app.scripts.import_products
.\.venv\Scripts\python.exe -m app.scripts.build_vector_index
```

导入脚本读取 `data/products.csv`，会跳过重复商品名称，因此可以重复运行。向量索引默认写入 `CHROMA_PERSIST_DIR`。

只更新指定商品的向量索引：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.build_vector_index --mode upsert --product-id 123
```

### Android

1. 使用 Android Studio 打开 `android-app/`。
2. 构建 Debug 包：

   ```powershell
   cd android-app
   .\gradlew.bat :app:assembleDebug
   ```

3. Android 模拟器访问本机后端时使用：

   ```text
   http://10.0.2.2:8000
   ```

当前 Android 客户端仍使用本地 mock 数据，真实后端联调会在后续里程碑接入。

## Docker

启动后端和 MySQL：

```powershell
docker compose up --build
```

容器启动后执行迁移和导入：

```powershell
docker compose exec backend python -m app.scripts.migrate_database
docker compose exec backend python -m app.scripts.import_products
docker compose exec backend python -m app.scripts.build_vector_index
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

- Backend: `http://127.0.0.1:8123`
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Grafana: `http://127.0.0.1:3000`，默认账号 `admin` / `admin`

## 验证

常用验证命令：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

本机临时目录权限异常时，可以将 pytest 临时目录切到仓库内：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_tmp\manual
```

一键验证：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

包含 Android 构建的一键验证：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall
```

## 浏览器检查

安装 Playwright Chromium：

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

检查本地 API 和文档页：

```powershell
.\.venv\Scripts\python.exe .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --record-video
```

使用已有 Chrome CDP：

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir=.chrome-agent
.\.venv\Scripts\python.exe .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --cdp-url http://127.0.0.1:9222
```

## 项目结构

```text
app/
  ai/             LLM、embedding、RAG 和 Agent 相关代码
  api/v1/         FastAPI v1 路由
  core/           配置、数据库、日志、错误和 provider
  integrations/   外部服务集成占位
  models/         SQLAlchemy ORM 模型
  repositories/   数据访问层
  schemas/        Pydantic API 契约
  services/       业务编排和用例逻辑
  scripts/        应用级脚本
  utils/          通用工具
  vectorstore/    ChromaDB 商品索引封装
android-app/      Kotlin Jetpack Compose 客户端
alembic/          数据库迁移
data/             Demo CSV 数据
docs/             架构、约定、计划和参考文档
observability/    Prometheus、Loki、Promtail、Grafana 配置
scripts/          仓库维护和验证脚本
tests/            后端测试
```

## 文档入口

- 系统概览：`docs/architecture/system-overview.md`
- 后端边界：`docs/architecture/backend-boundaries.md`
- Android 边界：`docs/architecture/android-boundaries.md`
- 运行和观测：`docs/architecture/runtime-observability.md`
- 产品规格：`docs/product/buywise-mvp.md`
- API 参考：`docs/reference/api.md`
- 配置参考：`docs/reference/configuration.md`
- 脚本参考：`docs/reference/scripts.md`

## 主要接口

所有公开 API 默认挂载在 `/api/v1` 下：

- `GET /api/v1/health`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/products`
- `POST /api/v1/products/compare`
- `POST /api/v1/ai/chat`
- `POST /api/v1/ai/chat/stream`
- `POST /api/v1/rag/search`
- `POST /api/v1/upload`
- `POST /api/v1/vision/recognize`
- `POST /api/v1/speech/asr`

## 开发约定

- 新后端路由放在 `app/api/v1/`，并在 `app/api/router.py` 注册。
- 业务逻辑放在 `app/services/`。
- 数据访问放在 `app/repositories/`。
- ORM 模型放在 `app/models/`。
- Pydantic schema 放在 `app/schemas/`。
- 测试放在 `tests/test_*.py`。
- Android 代码放在 `android-app/app/src/main/java/com/buywise/android/`。
- 认证、telemetry、日志和错误处理通过 `app.core.providers` 访问。
