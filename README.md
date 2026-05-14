# ShopAgent 后端与 Android 客户端

ShopAgent 是一个基于 FastAPI 的多模态（文本、视觉、语音）电商导购 Agent 方案，具备原生 Android 客户端。后端采用分层架构，支持大模型（LLM）、检索增强生成（RAG）、产品数据库、图片和语音分析等模块。

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

## Demo 产品数据导入

创建数据库表后，导入示例产品数据：

```powershell
.\.venv\Scripts\python.exe -m app.scripts.create_tables
.\.venv\Scripts\python.exe -m app.scripts.import_products
```

数据导入自动跳过同名产品，可多次执行。

---

## 功能模块

- **FastAPI 后端服务**：RESTful API & 分版本接口
- **Agent & LLM 集成**：聊天、产品咨询、对比、推荐等智能问答
- **RAG 检索增强生成**：产品知识库、向量数据库语义检索（Chroma）
- **产品/评论/价格历史管理**：ORM 全面支持产品、评论、推荐、价格历史、会话/消息
- **多模态接口**：图片理解（vision）、语音识别（腾讯 ASR）、文件上传
- **健康检查与测试路由**
- **安卓原生客户端**：Kotlin + Jetpack Compose，MVVM 架构
- **自动化脚本**：数据导入、数据库表创建、向量索引构建
- **文本构建工具**：`app/utils/text_builder.py` 提供结构化文本生成、用户需求检索表达等
- **RAG Pipeline**：`app/ai/rag_pipeline.py` 实现产品需求语义检索与动态过滤

---

## 目录结构

```text
app/
  ai/                     # 智能体、RAG、LLM、embedding 基础设施
    agent.py
    rag_pipeline.py       # RAG产品检索主流程
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
  integrations/           # 腾讯云、多模态API、Chroma等集成
  models/                 # ORM模型（Product、Review、Recommendation 等）
  repositories/           # 数据访问仓储
  schemas/                # Pydantic 数据结构
  services/               # 业务服务
  scripts/
    create_tables.py      # 数据库建表
    build_vector_index.py # 构建产品向量索引
    import_products.py    # 导入产品CSV
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

### 单元测试

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

- **AI 驱动 README 自动维护相关配置：**
  - 需在仓库 Secrets 配置 `GH_TOKEN`。
  - 自动维护基于 GitHub 扩展模型（非 OpenAI API）。
  - PR 标题/内容已全面中文自动生成。
- **RAG/Agent 能力：**
  - RAG 产品需求检索与筛选：详见 `app/ai/rag_pipeline.py`，支持用户需求结构自动提取、向量语义检索、候选商品多级过滤。
  - Agent 智能问答与任务编排：详见 `app/ai/agent.py`
- **多模态接口：**
  - 视觉（图片）、语音识别接口已预留并支持腾讯 ASR
- **文本组装工具**：  
  `app/utils/text_builder.py` 协助生成结构化查询文本，用于嵌入、检索和需求分析

---

## 贡献方式

- 提交请确保本地测试通过
- 欢迎扩展 Agent、RAG、产品数据结构等
- 如需支持或建议，请提交 issue

---
