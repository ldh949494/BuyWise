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

### Isolated PR environments

The compose stack is safe to run under a project name, so separate PRs can run
with independent containers, networks, and volumes:

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -Branch feature/pr-123 -BackendPort 8123 -MysqlPort 3323
```

The script creates a sibling Git worktree named `BuyWise-pr-123`, copies
`.env.dev.example` to `.env` if needed, then starts:

```powershell
docker compose -p buywise-pr-123 up -d --build
```

Stop the instance without removing data:

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123
```

Remove the containers, named volumes, and worktree:

```powershell
.\scripts\stop_pr_env.ps1 -Name pr-123 -RemoveVolumes -RemoveWorktree
```

### Browser validation

Install dependencies and the Chromium browser once:

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

Run a browser check against a local instance:

```powershell
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --record-video
```

The script validates `/api/v1/health`, opens `/docs`, saves a screenshot, and
writes a small DOM snapshot under `artifacts/browser`.

To attach to an existing Chrome started with CDP:

```powershell
chrome.exe --remote-debugging-port=9222 --user-data-dir=.chrome-agent
python .\scripts\browser_check.py --base-url http://127.0.0.1:8123 --cdp-url http://127.0.0.1:9222
```

### Observability

Start a PR instance with Prometheus, Loki, Promtail, and Grafana:

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

Default local ports:

- Backend: `http://127.0.0.1:8123`
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Grafana: `http://127.0.0.1:3000` (`admin` / `admin`)

The FastAPI app exposes Prometheus metrics at `/metrics`. Application logs are
emitted as JSON to stdout, and Promtail labels Docker logs with compose project
and service names. Useful queries:

```logql
{compose_project="buywise-pr-123", service="backend"} |= "ERROR"
```

```promql
rate(http_requests_total[5m])
```

## Project Layout

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

## 自动化验证与 AI README 维护

- **本地自动化校验**：

  ```
  powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1
  ```

- **GitHub Actions**：  
  `.github/workflows/ai-auto-commit.yml`  
  支持 main 分支 push 或手动触发时，执行本地校验与 AI 自动维护 README。只在有真实内容变更时创建 PR。Pull Request 标题与说明自动生成。

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

### 数据库表结构初始化

```
python app/scripts/create_tables.py
```

### 构建产品向量索引（RAG）

- 推荐每次商品表变动后重新同步索引：

  ```
  python app/scripts/build_vector_index.py
  ```

  支持从数据库同步所有产品，并更新嵌入向量及语义检索索引。

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

- **AI-Driven README 更新需配置：**
  - 在仓库 Secrets 配置 `GH_TOKEN`（GitHub Actions 自动化令牌）。
  - 自动维护脚本现在基于 GitHub 模型扩展（`gh models`），不再使用 OpenAI 直连变量。
  - Pull Request 标题与说明、README 更新 PR 说明模板已全面适配简体中文。
- **RAG/Agent 能力在 `app/ai/agent.py`、`app/ai/rag_pipeline.py`、`vectorstore/chroma_client.py`（检索与嵌入）、`ai/embedding_client.py`（embedding 算法实现）模块实现。**
- **多模态相关：**
  - 视觉接口（`vision.py`，`app/services/vision_service.py`）：支持图像类别/特征抽取（当前为 mock，可扩展多模态模型）
  - 语音 ASR（`speech.py`，`app/services/speech_service.py`）：支持语音转文本（当前为 mock，可对接腾讯ASR）
  - 文件上传（`upload.py`，`app/services/upload_service.py`）：支持文件本地存储及后续扩展云存储
- **文本组装工具**：  
  `app/utils/text_builder.py` 协助生成结构化查询文本，用于嵌入、检索和需求分析
- **意图识别与需求结构化**：  
  `app/services/intent_service.py` 新增规则与轻量 LLM 结合的用户意图/需求要素抽取，准确处理“推荐/对比/平替/价格/参数”等消费问询，提取 product category、场景、预算、偏好字段，支持灰度部署未来 LLM 结构化助手。
- **推荐服务说明**：
  - `app/services/recommend_service.py` 提供智能商品推荐排序，综合考虑用户预算、偏好、适用场景、评分、销量和库存，生成多因子排序及推荐理由说明。
- **LLM 智能输出能力说明：**
  - `app/ai/llm_client.py` 新增结构化方法，涵盖推荐理由、自然语言澄清追问、商品对比总结生成，辅助 UI 端输出和 Agent 智能交互。  
  - Prompt 模板集中于 `app/ai/prompts.py`，支持结构化意图抽取、推荐、对比和澄清场景。

---

## 贡献方式

- 提交请确保本地测试通过
- 欢迎扩展 Agent、RAG、产品数据结构等
- 如需支持或建议，请提交 issue

---
