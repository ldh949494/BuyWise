# ShopAgent 后端与 Android 客户端

ShopAgent 是一个基于 FastAPI 的多模态（文本、视觉、语音）电商导购 Agent 解决方案，具备原生 Android 客户端。后端采用分层架构，支持大模型（LLM）、检索增强生成（RAG）、产品数据库、图片和语音分析等模块。

---

## 快速启动

### Python FastAPI 后端

1. 建立并激活 Python 虚拟环境。
2. 安装后端依赖：

   ```
   pip install -r requirements.txt
   ```

3. （可选）复制 `.env.example` 为 `.env`，调整配置。
4. 启动 API 服务：

   ```
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```

5. 打开 API 文档与健康检查：
   - API 文档：http://127.0.0.1:8000/docs
   - 健康检查：http://127.0.0.1:8000/api/v1/health

6. 数据库初始化（首次建议手动执行）：

   ```
   python app/scripts/create_tables.py
   ```

### 原生 Android 客户端

1. 用 Android Studio 打开 `android-app/` 目录运行项目。
2. 或命令行编译调试版本：

   ```
   cd android-app
   .\gradlew.bat :app:assembleDebug
   ```

3. 默认后端访问地址（适配安卓模拟器）为：

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

如需构建/更新产品向量检索索引（RAG），执行：

```powershell
python app/scripts/build_vector_index.py
```

脚本将自动从数据库读取所有产品，调用内置 embedding 客户端，构建向量并存入内存型向量库（仿 Chroma）。
支持二次多次构建，便于开发调试。

---

## 功能模块

- **FastAPI 后端服务**：RESTful、分版本 API 接口布局
- **Agent & LLM 集成**：聊天、产品咨询、比较、推荐等智能问答
- **RAG 检索增强生成**：产品知识库及向量数据库语义检索（内存型 Chroma 仓储，embedding、search已实现）
- **产品信息/评论/价格历史/推荐管理**：全功能 ORM 支持产品、评论、推荐、价格历史、会话/消息全模型
- **多模态接口**：
  - **图片理解**：`/api/v1/vision/recognize`（输入 image_url，返回类别、特征、query）
  - **语音识别**：`/api/v1/speech/asr`（输入 audio_url，返回文本）
  - **文件上传**：`/api/v1/upload/upload`（支持图片/音频文件，本地存储返回访问 URL）
- **健康检查与测试路由**
- **安卓原生客户端**：Kotlin + Jetpack Compose，MVVM 架构
- **自动化脚本**：数据导入、数据库表创建、向量索引构建
- **文本构建工具**：`app/utils/text_builder.py` 提供结构化文本生成、用户需求检索表达等
- **RAG Pipeline**：`app/ai/rag_pipeline.py` 实现产品需求语义检索与动态过滤
- **意图识别服务**：`app/services/intent_service.py` 支持商品推荐/对比/找平替等场景的意图、分类、预算、场景和偏好抽取
- **智能推荐服务**：`app/services/recommend_service.py` 根据预算、场景、偏好、销量、库存等多因素商品排序推荐理由
- **LLM 智能回复与总结生成**：`app/ai/llm_client.py` 支持 mock/后续替换大模型，实现推荐理由生成、需求澄清、商品对比总结 

---

### PR 独立环境启动

Compose 支持不同项目名多环境，PR 可独立运行容器、网络、存储：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -Branch feature/pr-123 -BackendPort 8123 -MysqlPort 3323
```

脚本会创建对等 Git 工作区 BuyWise-pr-123，必要时复制 `.env.dev.example`，然后启动：

```powershell
docker compose -p buywise-pr-123 up -d --build
```

停止实例但保留数据：

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

开启本地 API 服务后执行：

```powershell
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --record-video
```

自动访问 `/api/v1/health`， `/docs`，截图并生成快照到 `artifacts/browser`。

附加已启动 CDP 的 Chrome：

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir=.chrome-agent
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --cdp-url http://127.0.0.1:9222
```

### 观测性支持

PR 环境可一键启动 Prometheus、Loki、Promtail、Grafana：

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

默认端口：

- 后端: `http://127.0.0.1:8123`
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Grafana: `http://127.0.0.1:3000` (`admin` / `admin`)

FastAPI 提供 `/metrics` Prometheus 监控接口。应用日志以 JSON 输出，Promtail 按 compose 标签采集。

Loki 查询示例:

```logql
{compose_project="buywise-pr-123", service="backend"} |= "ERROR"
```

Prometheus 查询示例:

```promql
rate(http_requests_total[5m])
```

## 项目结构

```text
app/
  ai/                     # 智能体基础设施（agent、RAG、LLM、embedding，embedding_client.py 实现embed）
    llm_client.py         # LLM结构化推荐/对比/澄清理由与问句生成（Mock模式，后续可接大模型API）
    prompts.py            # LLM Prompt模版
    agent.py              # 任务式Agent主逻辑
    rag_pipeline.py       # RAG语义检索与候选集过滤
  api/                    # FastAPI 路由与 API 逻辑
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
  integrations/           # 外部系统集成，如腾讯云、Chroma、ASR、多模态API
  models/                 # ORM 数据模型（Product、Review、Recommendation、PriceHistory、ChatSession、ChatMessage 等）
  repositories/           # 数据库仓储模式
  schemas/                # Pydantic 读写数据结构
  services/               # 业务服务层 (chat、product、recommend、intent等)
    intent_service.py     # 意图检测/需求解析（规则+LLM 提取，全面覆盖主流消费问询）
    recommend_service.py  # 推荐服务（推荐理由生成、智能商品排名）
    upload_service.py     # 文件上传服务（本地/云存储）
    vision_service.py     # 图像理解服务（类别和特征抽取）
    speech_service.py     # 语音转文本服务（ASR）
  scripts/                # 运维和数据脚本
    create_tables.py      # 数据库表自动创建
    build_vector_index.py # 构建产品向量索引，生成RAG语义检索索引
    import_products.py
    seed_products.py
  utils/
    text_builder.py       # 商品文本和检索需求拼装
  vectorstore/
    chroma_client.py      # Chroma向量存储接口
    product_index.py
android-app/              # 安卓客户端（Kotlin/Jetpack Compose/MVVM）
.github/workflows/        # GitHub Actions
requirements.txt          # Python依赖
```

---

## 自动化校验与 AI 维护

### 本地自动化校验

```
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1
```

- 脚本会自动检查依赖、环境变量、仓库文档结构及链接有效性。
- 文档校验采用 `scripts/validate_docs.py`，包含：
  - AGENTS.md 映射导航检查
  - docs/ 子目录结构与链接目标检测
  - Feature design 文档状态（Status 行）校验

### GitHub Actions 自动维护（AI README/文档修剪）

- `.github/workflows/ai-auto-commit.yml`，push 或手动触发时检出主分支，自动校验并根据 diff/代码变更维护 README。
- 支持可选 doc-gardening report（手动/自动 AI 分析建议）。
- 经 AI 推荐的文档内容须经人工复核后用命令应用：

  ```powershell
  python .\scripts\doc_gardening.py --apply
  ```

- 所有改动分新分支提交，只对有真实内容变更时发起 PR。PR 标题、说明、README Diff 说明自动生成。

### 仓库记忆 (Repository memory)

Agent-facing 项目记忆为模块化导航结构：

- `AGENTS.md`: 智能体和开发者定位的入口速查
- `docs/architecture/`: 核心模块边界说明
- `docs/design/`: 功能设计与状态标注
- `docs/conventions/`: 代码、测试、文档规范
- `docs/plans/`: 实现/演进方案
- `docs/reference/`: 脚本、API、配置参数参考

可使用如下指令校验记忆结构与有效性：

```powershell
python .\scripts\validate_docs.py
```

生成一次 doc-gardening AI 检查建议：

```powershell
python .\scripts\doc_gardening.py
```

---

## FastAPI 多模态接口说明

- `/api/v1/health` 健康检查
- `/api/v1/chat` 智能聊天&问答
- `/api/v1/products` 商品信息/检索
- `/api/v1/compare` 商品对比分析
- `/api/v1/rag` 检索增强生成
- `/api/v1/upload/upload` 文件上传（支持图片/音频等二进制，返回文件访问路径）
- `/api/v1/vision/recognize` 图像识别/类目&属性解析
- `/api/v1/speech/asr` 语音识别转文本（Mock/后续可对接腾讯ASR）

---

## 开发与测试说明

### 启动 FastAPI 服务

```
uvicorn app.main:app --reload --port 8000
```

> 生产建议 WSGI/ASGI 部署，并配置安全数据库。

### 仓库文档校验与 AI Doc-gardening

- 校验项目文档结构与内容：

  ```
  python .\scripts\validate_docs.py
  ```

Validate Provider-mode boundaries for cross-cutting concerns:

```powershell
python .\scripts\validate_providers.py
```

Run the custom repository linter:

```powershell
python .\scripts\validate_repo_lint.py
```

Generate a manual doc-gardening report:

  ```
  python .\scripts\doc_gardening.py
  ```

- 审核后应用 AI 提交建议的文档改动：

  ```
  python .\scripts\doc_gardening.py --apply
  ```

### 数据库表结构初始化

```
python app/scripts/create_tables.py
```

### 构建产品向量索引（RAG）

- 商品表变动后请重新同步索引：

  ```
  python app/scripts/build_vector_index.py
  ```

  从数据库同步所有产品并更新嵌入向量及语义检索索引。

### 运行单元测试

- 推荐创建 `tests/` 目录，使用：

  ```
  pytest -q
  ```

- 自动化脚本同样会检测、运行单元测试

### 构建 Android 客户端

```
cd android-app
.\gradlew.bat :app:assembleDebug
```
也可用 Android Studio 图形界面

---

## 重要说明

- **AI-Driven README/文档维护需配置：**
  - 仓库 Secrets 配置 `GH_TOKEN`（GitHub Actions 自动化令牌）。
  - 自动维护脚本基于 GitHub 模型扩展（`gh models`），无需单独配置 OpenAI Key。
  - PR 标题与说明、README 更新说明 PR 模板全面适配简体中文。
- **RAG/Agent 能力在 `app/ai/agent.py`、`app/ai/rag_pipeline.py`、`vectorstore/chroma_client.py`（检索与嵌入）、`ai/embedding_client.py`（embedding 算法实现）模块实现。**
- **多模态相关能力：**
  - 视觉接口（`vision.py`, `app/services/vision_service.py`）：支持图像类别/特征抽取（Mock，可扩展成多模态模型）
  - 语音 ASR（`speech.py`, `app/services/speech_service.py`）：支持语音转文本（Mock，支持腾讯ASR扩展）
  - 文件上传（`upload.py`, `app/services/upload_service.py`）：支持本地存储及后续云存储扩展
- **文本组装工具**  
  `app/utils/text_builder.py` 用于生成结构化检索/嵌入文本，支撑 RAG 语义检索和需求分析
- **意图识别与需求结构化**  
  `app/services/intent_service.py`：规则+LLM 结合的意图/需求抽取，全面覆盖推荐/对比/平替等消费问询场景，提取品类、场景、预算、偏好字段，为后续 LLM 助手灰度升级打基础
- **推荐服务说明**
  - `app/services/recommend_service.py` 智能多因子商品推荐，结合用户预算、场景、偏好、销量、库存等，生成推荐理由与排序
- **LLM 智能输出说明**
  - `app/ai/llm_client.py`：结构化推荐理由、追问澄清、商品对比摘要生成（Mock，可插拔 LLM），面向 UI/Agent 智能交互
  - Prompt 模板集中于 `app/ai/prompts.py`，统一意图抽取、推荐、对比、澄清等场景书写与复用

---

## 贡献方式

- 提交前请确保本地测试和文档校验通过
- 鼓励扩展 Agent、RAG、产品数据结构等核心模块
- 建议/疑问请提交 issue

---
