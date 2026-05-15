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
- **统一 Provider 管理**：`app/core/providers.py` 提供跨领域能力分离，集中管理 logging/telemetry/auth/errors 等横切关注点（详见自动化校验说明）

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

启动 PR 实例时包含 Prometheus/Loki/Promtail/Grafana:

```powershell
.\scripts\start_pr_env.ps1 -Name pr-123 -BackendPort 8123 -MysqlPort 3323 -Observability
```

默认本地端口：

- 后端: `http://127.0.0.1:8123`
- Prometheus: `http://127.0.0.1:9090`
- Loki: `http://127.0.0.1:3100`
- Grafana: `http://127.0.0.1:3000` (`admin` / `admin`)

FastAPI 应用自动暴露 `/metrics` Prometheus 指标。应用日志全部以 JSON 格式写入 stdout，Promtail 自动绑定 compose 项目/服务等 labels，便于云原生可观测性。
常用日志/监控查询：

```logql
{compose_project="buywise-pr-123", service="backend"} |= "ERROR"
```

```promql
rate(http_requests_total[5m])
```

---

## Project Layout

```text
app/
  ai/                     # 智能体基础设施（agent、RAG、LLM、embedding）
    llm_client.py         # LLM结构化推荐/对比/澄清理由与问句生成（Mock或对接API）
    prompts.py
    agent.py
    rag_pipeline.py
    embedding_client.py
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
    logging.py            # 日志封装器（已适配 provider 方案）
    exceptions.py
    providers.py          # 横切关注点统一声明: 日志/监控/异常/认证
  integrations/           # 云服务、Chroma等集成
  models/                 # ORM 数据模型
  repositories/
  schemas/
  services/
    intent_service.py     
    recommend_service.py  
    upload_service.py     
    vision_service.py     
    speech_service.py
  scripts/
    create_tables.py      
    build_vector_index.py 
    import_products.py
    seed_products.py
  utils/
    logging.py            # 日志适配器接口
    text_builder.py
  vectorstore/
    chroma_client.py
    product_index.py
android-app/              # 安卓客户端 (Kotlin/Jetpack Compose/MVVM)
.github/workflows/        # CI/CD 工作流
requirements.txt          # Python依赖
```

---

## 自动化验证与 AI README 维护

- **本地自动化校验**：

  ```powershell
  powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1
  ```

  - 自动执行依赖、数据库、Provider 边界和文档校验

- **文档校验、Provider 校验单独命令**：

  ```powershell
  python .\scripts\validate_docs.py
  python .\scripts\validate_providers.py
  ```

  - validate_providers.py 可自动发现非法跨 Provider 导入，避免横切关注点滥用

- **GitHub Actions**：  
  `.github/workflows/ai-auto-commit.yml`  
  支持 main 分支 push 或手动触发时，执行本地校验与 AI 自动维护 README。只在有真实内容变更时创建 PR。Pull Request 标题与说明自动生成。

- **AI-Driven README 更新需配置：**
  - 在仓库 Secrets 配置 `GH_TOKEN`（GitHub Actions 自动化令牌）。
  - 自动维护脚本基于 GitHub 模型扩展（`gh models`），无需 OpenAI 直连变量。
  - Pull Request 标题与说明、README 更新 PR 说明模板，适配简体中文。

---

## FastAPI 多模态接口说明

- `/api/v1/health` 健康检查
- `/api/v1/chat` 智能聊天&问答
- `/api/v1/products` 商品信息&检索
- `/api/v1/compare` 商品对比分析
- `/api/v1/rag` 检索增强生成
- `/api/v1/upload/upload` 文件上传（支持图片/音频等二进制，返回文件访问路径）
- `/api/v1/vision/recognize` 图像识别/类目&属性解析
- `/api/v1/speech/asr` 语音识别转文本（Mock/可对接腾讯ASR）

---

## 开发与测试说明

### 启动 FastAPI 服务

```
uvicorn app.main:app --reload --port 8000
```

> 生产建议 WSGI/ASGI 部署，并配置安全数据库。

### Provider 边界/横切关注点约束说明

- **日志接口**：统一通过 `app/core/providers.py` 或 `app/utils/logging.py` 获取，不允许直接 import logging
- **监控埋点**：通过 provider 获取，只允许统一封装后使用
- **自动化校验**：`scripts/validate_providers.py` 强制检测模块边界，如发现违规直接提示需整改

### Repository memory

Agent-facing project memory follows a map-based structure:

- `AGENTS.md`: 紧凑的 Agent 入口文档
- `docs/architecture/`: 模块边界说明
- `docs/design/`: 设计方案与验收状态
- `docs/conventions/`: 编码/测试/文档规范
- `docs/plans/`: 实现计划
- `docs/reference/`: API、配置、脚本说明

验证文档：

```powershell
python .\scripts\validate_docs.py
```

Provider 横切关注点检测：

```powershell
python .\scripts\validate_providers.py
```

生成文档维护建议报告：

```powershell
python .\scripts\doc_gardening.py
```

应用 AI 补丁：

```powershell
python .\scripts\doc_gardening.py --apply
```

### Local validation

```
python app/scripts/create_tables.py
```

### 构建产品向量索引（RAG）

推荐每次商品表变动后重新同步索引：

```
python app/scripts/build_vector_index.py
```

支持数据库同步所有产品，并更新嵌入向量及语义检索索引。

### 运行单元测试

建议建立 `tests/` 目录，运行：

```
pytest -q
```

脚本亦会自动化检测所有测试。

### 构建 Android 客户端

```
cd android-app
.\gradlew.bat :app:assembleDebug
```
或使用 Android Studio 可视化构建与调试。

---

## 重要说明

- **Provider/横切关注点能力在 `app/core/providers.py` 集中实现：**
  - logging / telemetry / errors / auth 统一注册、可插拔，相关模块只允许通过 providers 获取
  - 采用自动化校验强制约束边界，便于可观测性与安全
- **RAG/Agent 能力在 `app/ai/agent.py`、`app/ai/rag_pipeline.py`、`vectorstore/chroma_client.py`、`app/ai/embedding_client.py` 植入**
- **多模态相关**：
  - 视觉：`vision.py`、`app/services/vision_service.py`
  - 语音 ASR：`speech.py`、`app/services/speech_service.py`
  - 文件上传：`upload.py`、`app/services/upload_service.py`
- **文本组装**：`app/utils/text_builder.py` 用于嵌入与检索表达结构化拼装
- **意图识别与需求结构化**：`app/services/intent_service.py`，LLM/规则混合抽取用户消费意图、商品范畴、预算、喜欢字段
- **推荐服务说明**：`app/services/recommend_service.py` 综合预算/场景/评分等多因子排序并理由说明
- **LLM 智能输出**：`app/ai/llm_client.py` 输出推荐理由、追问、对比总结，Prompt 模板见 `app/ai/prompts.py`

---

## 贡献方式

- 提交前请确保本地测试 & 校验通过
- 欢迎扩展 Agent、RAG、产品数据结构等边界
- 如需技术支持或有建议，请提交 issue

---
