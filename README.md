# ShopAgent 后端与 Android 客户端

ShopAgent 是一个基于 FastAPI 的多模态（文本、视觉、语音）电商导购 Agent 解决方案，拥有原生 Android 客户端。后端采用分层架构，支持大模型（LLM）、检索增强生成（RAG）、产品数据库、图片和语音分析等模块。

---

## 快速启动

### Python FastAPI 后端

1. 建立并激活 Python 虚拟环境。
2. 安装后端依赖：

   ```
   pip install -r requirements.txt
   ```

3. （可选）复制 `.env.example` 为 `.env`，调整配置项。
4. 启动 API 服务：

   ```
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```

5. 打开 API 文档与健康检查：
   - API 文档：http://127.0.0.1:8000/docs
   - 健康检查：http://127.0.0.1:8000/api/v1/health

6. 数据库初始化（首次请手动执行一次）：

   ```
   python app/scripts/create_tables.py
   ```

### 原生 Android 客户端

1. 用 Android Studio 打开 `android-app/` 目录直接运行项目。
2. 或命令行编译调试版本：

   ```
   cd android-app
   .\gradlew.bat :app:assembleDebug
   ```

3. 默认后端访问地址（安卓模拟器默认内网映射）：

   ```
   http://10.0.2.2:8000
   ```

---

## Demo Product Data

初始化数据库表后导入示例产品数据：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.create_tables
.\.venv\Scripts\python.exe -m app.scripts.import_products
```

导入器自动读取 `data/products.csv`，跳过重复产品名，可多次执行。

---

## 向量索引构建（RAG 支持）

如需构建/更新产品向量检索索引（RAG），请执行：

```powershell
python app/scripts/build_vector_index.py
```

脚本会自动从数据库读取所有产品，调用内置 embedding 客户端，构建向量并存入内存型向量库（仿 Chroma）。
支持二次多次构建，便于开发调试。

---

## 功能模块

- **FastAPI 后端服务**：RESTful、多版本 API 路由
- **Agent & LLM 集成**：智能聊天、产品咨询、对比、推荐等问答
- **RAG 检索增强生成**：产品知识库向量数据库语义检索（内存型 Chroma 仓储、embedding、search 已实现）
- **产品信息/评论/价格历史/推荐管理**：全功能 ORM 支持产品、评论、推荐、价格历史、会话/消息等全模型
- **多模态接口**：
  - **图片理解**：`/api/v1/vision/recognize`（输入 image_url，返回类别、特征、query）
  - **语音识别**：`/api/v1/speech/asr`（输入 audio_url，返回文本）
  - **文件上传**：`/api/v1/upload/upload`（支持图片/音频文件，本地存储返回访问 URL）
- **健康检查与测试路由**
- **安卓原生客户端**：Kotlin + Jetpack Compose，MVVM 架构
- **自动化脚本**：数据导入、数据库表创建、向量索引构建
- **文本构建工具**：`app/utils/text_builder.py` 提供结构化文本生成、用户需求检索表达等
- **RAG Pipeline**：`app/ai/rag_pipeline.py` 实现产品需求语义检索与动态过滤
- **意图识别服务**：`app/services/intent_service.py` 支持推荐/对比/平替等消费场景的意图、分类、预算、场景和偏好字段自动抽取
- **智能推荐服务**：`app/services/recommend_service.py` 根据预算、场景、偏好、销量、库存等多因素商品推荐及理由生成
- **LLM 智能回复与摘要生成**：`app/ai/llm_client.py` 支持 mock/可替换大模型，结构化推荐理由/追问/商品对比结果输出

---

### PR 独立环境启动

Compose 支持多环境，PR 可独立运行容器、网络、存储：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -Branch feature/pr-123 -BackendPort 8123 -MysqlPort 3323
```

脚本会创建对应 Git 工作区 BuyWise-pr-123，自动复制 `.env.dev.example`，并启动：

```powershell
docker compose -p buywise-pr-123 up -d --build
```

停止环境但保留数据：

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123
```

移除容器、数据卷和工作区：

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123 -RemoveVolumes -RemoveWorktree
```

### 浏览器端校验

一次性安装依赖与 chromium 浏览器：

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

本地开启 API 服务后：

```powershell
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --record-video
```

自动访问 `/api/v1/health`、`/docs` 并截图生成快照到 `artifacts/browser`。

附加已启动 CDP 的 Chrome：

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir=.chrome-agent
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --cdp-url http://127.0.0.1:9222
```

### 观测性支持

PR 环境支持一键启动 Prometheus、Loki、Promtail、Grafana：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

默认端口分布：

- 后端: `http://127.0.0.1:8123`
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Grafana: `http://127.0.0.1:3000`（`admin` / `admin`）

FastAPI 提供 `/metrics` Prometheus 监控接口。所有应用日志以 JSON 输出，Promtail 采集 compose 标签。

Loki 查询：

```logql
{compose_project="buywise-pr-123", service="backend"} |= "ERROR"
```

Prometheus 查询：

```promql
rate(http_requests_total[5m])
```

## 项目结构

```text
app/
  ai/                     # 智能体基础设施（agent、RAG、LLM、embedding）
    llm_client.py         # LLM 推荐/对比/澄清理由，Mock 可扩展为接入大模型
    prompts.py
    agent.py
    rag_pipeline.py
  api/
    router.py
    v1/
      health.py
      chat.py
      products.py
      rag.py
      compare.py
      upload.py
      vision.py
      speech.py
  core/
    config.py
    database.py
    logging.py
    exceptions.py
  integrations/           # 腾讯云/Chroma/ASR/多模态等集成
  models/                 # ORM 实体（Product、Review、Recommendation、PriceHistory、ChatSession、ChatMessage等）
  repositories/           # 仓储数据层
  schemas/                # Pydantic 数据结构
  services/               # 业务服务 (chat、product、recommend、intent等)
    rag_service.py        # RAG 业务服务逻辑（语义检索及向量索引fallback分流）
    intent_service.py
    recommend_service.py
    upload_service.py
    vision_service.py
    speech_service.py
  scripts/
    create_tables.py      # 数据库表创建
    build_vector_index.py # 产品embedding/向量索引构建
    import_products.py
    seed_products.py
  utils/
    text_builder.py
  vectorstore/
    chroma_client.py      # 向量存储接口
    product_index.py
android-app/              # 安卓客户端
.github/workflows/
requirements.txt
```

---

## 自动化校验与 AI 文档维护

### 本地自动化校验

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1
```

- 自动检查依赖、环境变量、仓库文档结构及链接有效性
- 文档校验用 `scripts/validate_docs.py`，包括：
  - AGENTS.md 导航映射检查
  - docs/ 结构与链接目标校验
  - Feature 设计文档状态校验

Validate Provider 模式边界：

```powershell
python .\scripts\validate_providers.py
```

自定义仓库 Lint 校验：

```powershell
python .\scripts\validate_repo_lint.py
```

人工触发 AI Doc-gardening 检查建议：

```powershell
python .\scripts\doc_gardening.py
```

- 实审后应用 AI 提议的文档改动：

  ```
  python .\scripts\doc_gardening.py --apply
  ```

### 仓库记忆导航

- `AGENTS.md`: 智能体与开发入口
- `docs/architecture/`: 结构边界说明
- `docs/design/`: 功能设计与状态
- `docs/conventions/`: 代码/测试/文档规范
- `docs/plans/`: 方案和演进
- `docs/reference/`: API、配置等文档

校验指令：

```powershell
python .\scripts\validate_docs.py
```

---

## FastAPI 多模态接口大纲

- `/api/v1/health` 健康检查
- `/api/v1/chat` 智能对话
- `/api/v1/products` 查询商品
- `/api/v1/compare` 商品对比
- `/api/v1/rag` 检索增强生成
- `/api/v1/upload/upload` 文件上传（图片/音频）
- `/api/v1/vision/recognize` 图像解析
- `/api/v1/speech/asr` 语音转文本（Mock/可扩展对接腾讯ASR）

---

## 开发与测试说明

### 启动 FastAPI 服务

```
uvicorn app.main:app --reload --port 8000
```

> 生产环境请使用 WSGI/ASGI 部署，配置安全数据库。

### 文档校验与 AI Doc-gardening

```
python .\scripts\validate_docs.py
```

Validate Provider 校验：

```powershell
python .\scripts\validate_providers.py
```

自定义仓库 Lint 检查：

```powershell
python .\scripts\validate_repo_lint.py
```

Validate entropy rules and generate a cleanup report:

```powershell
python .\scripts\validate_entropy.py
python .\scripts\entropy_gc.py
```

Generate a manual doc-gardening report:

```
python .\scripts\doc_gardening.py
```

应用 AI 修订建议：

```
python .\scripts\doc_gardening.py --apply
```

### 数据库表初始化

```
python app/scripts/create_tables.py
```

### 构建产品向量索引（RAG）

```
python app/scripts/build_vector_index.py
```

数据库产品变更后请同步索引。

### 运行测试

建议新建 `tests/` 目录，运行：

```
pytest -q
```

### 构建 Android 客户端

```
cd android-app
.\gradlew.bat :app:assembleDebug
```
或使用 Android Studio

---

## 重要说明

- **AI-Driven README/文档维护**
  - 仓库 Secrets 需配置 GH_TOKEN（GitHub Actions 自动化令牌）
  - 维护脚本用 GitHub 模型，无需独立 OpenAI Key
  - PR 模板、描述支持中文
- **RAG/Agent 能力核心实现：**
  - `app/ai/agent.py`、`app/ai/rag_pipeline.py`
  - `vectorstore/chroma_client.py`（向量检索/embedding）
  - `app/ai/embedding_client.py`（embedding 算法）
- **多模态相关功能：**
  - 视觉接口（`vision.py`, `services/vision_service.py`）：图片类目/特征提取（Mock 可扩展多模态）
  - 语音 ASR（`speech.py`, `services/speech_service.py`）：语音文本（Mock，支持腾讯ASR扩展）
  - 文件上传（`upload.py`, `services/upload_service.py`）：支持本地/云存储
- **文本组装工具**：`app/utils/text_builder.py`
- **意图识别与需求结构化**：`app/services/intent_service.py`
- **推荐服务**：`app/services/recommend_service.py`
- **LLM 智能输出**：`app/ai/llm_client.py`, `app/ai/prompts.py`

---

## 贡献指南

- 提交前请确保本地测试、自动化校验全部通过
- 欢迎扩展 Agent、RAG、商品结构等核心功能
- 建议/疑问请提交 issue

---
