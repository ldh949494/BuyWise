# ShopAgent 后端与 Android 客户端

ShopAgent 是一个基于 FastAPI 的多模态（文本、视觉、语音）电商导购 Agent 解决方案，且支持原生 Android 客户端。后端采用分层架构，具备高扩展性，集成大模型（LLM）、文档向量检索（RAG）、产品数据库、图片和语音分析等功能模块。

---

## 快速启动

### Python FastAPI 后端

1. 建立 Python 虚拟环境并激活。
2. 安装依赖：

   ```
   pip install -r requirements.txt
   ```

3. （可选）复制 `.env.example` 为 `.env` 并根据需求调整配置变量。
4. 启动 API 服务：

   ```
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```

5. 打开接口文档和健康检查：
   - API 文档地址: http://127.0.0.1:8000/docs
   - 健康检查: http://127.0.0.1:8000/api/v1/health

6. 数据库初始化：  
   在首次启动时自动创建表。也可手动执行：

   ```
   python app/scripts/create_tables.py
   ```

### 原生 Android 客户端

1. 推荐使用 Android Studio 打开 `android-app/` 目录运行项目。
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
- **产品信息/评论/价格历史管理**：全功能 ORM 支持产品、评论、推荐、价格历史、会话/消息全模型
- **多模态接口**：图片理解、语音识别（集成腾讯 ASR）、文件上传
- **健康检查与测试路由**
- **安卓原生客户端**：Kotlin、Jetpack Compose、MVVM 架构，支持首页、AI 导购、产品对比、详情页、视觉入口等
- **自动化脚本**：数据导入、创建数据库表、向量索引构建等

---

## 目录结构

```text
app/
  ai/                     # 智能体基础设施（agent、RAG、LLM、embedding，新增 embedding_client.py 实现）
  api/                    # FastAPI 路由与 API 逻辑
    router.py
    v1/                   # 版本化接口分发
      health.py
      chat.py
      products.py
      rag.py
      compare.py
      upload.py
      vision.py
      speech.py
  core/                   # 配置、数据库、日志、异常
    config.py
    database.py
    logging.py
    exceptions.py
  integrations/           # 外部系统集成，如腾讯云、Chroma、ASR、多模态API
  models/                 # ORM 数据模型（Product、Review、Recommendation、PriceHistory、ChatSession、ChatMessage 等）
  repositories/           # 数据库仓储模式
  schemas/                # Pydantic 读写数据结构
  services/               # 业务服务层 (chat、product、recommend等)
  scripts/                # 运维和数据脚本
    create_tables.py      # 数据库表自动创建
    build_vector_index.py # 构建产品向量索引，生成RAG语义检索索引（已实现）
    import_products.py
    seed_products.py
  utils/                  # 工具函数库
  vectorstore/            # 向量数据库及索引工具（ChromaProductStore 实现 embedding/检索）
android-app/              # 安卓原生客户端，Kotlin/Jetpack Compose 实现
.github/workflows/        # GitHub Actions 自动化工作流
requirements.txt          # Python依赖
```

---

## 自动化验证与 AI README 维护

- **本地验证**：  
  运行自动化脚本一键校验基础功能（依赖安装、API 连通性、接口正确性、单元测试、Android 构建）。
  
  ```
  powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1
  ```

- **自动化工作流**：  
  `.github/workflows/ai-auto-commit.yml`  
  支持 main 分支 push 或手动触发时，自动执行本地校验和基于变更的 AI README 自动维护脚本。只有 README 有真实更新时才会自动提交并创建 PR。
  - 所有 Pull Request 标题和说明、README 更新 PR 说明，均自动由 AI 按中文模板生成。

---

## 开发与测试说明

### 启动 FastAPI 服务

```
uvicorn app.main:app --reload --port 8000
```

> 生产环境请使用 WSGI/ASGI 服务器和配置安全数据库。

### 数据库表结构初始化

- 推荐手动或自动执行脚本：

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

- 推荐目录自建 `tests/` 并通过：

  ```
  pytest -q
  ```

- 自动化脚本会自动检测和运行 `pytest`

### 构建 Android 客户端

```
cd android-app
.\gradlew.bat :app:assembleDebug
```
或用 Android Studio！

---

## 重要说明

- **AI-Driven README 更新需配置：**
  - 在仓库 Secrets 配置 `GH_TOKEN`（GitHub Actions 自动化令牌）。
  - 自动维护脚本现在基于 GitHub 模型扩展（`gh models`），不再使用 OpenAI 直连变量。
  - Pull Request 标题与说明、README 更新 PR 说明模板已全面适配简体中文。
- **RAG/Agent 能力在 `app/ai/agent.py`、`app/ai/rag_pipeline.py`、`vectorstore/chroma_client.py`（检索与嵌入）、`ai/embedding_client.py`（embedding 算法实现）模块实现。**
- **多模态相关：**
  - 视觉接口（`vision.py`）、语音 ASR（`speech.py`）和产品图片等接口已预留或初步实现。

---

## 贡献方式

- 提交代码请确保本地测试通过。
- 可自定义/扩展 agent、RAG、产品模型等。
- 若需补充说明或有问题，可提 issue。

---
