# 设计：内部后台管理台

Status: Draft

## 背景

BuyWise 当前具备 FastAPI 后端、Android 客户端、商品维护 API、上传接口和商品索引同步能力，但没有单独的可视化后台管理系统。内部开发和运营测试人员需要更直观地维护演示商品数据，避免长期依赖脚本、OpenAPI 页面或手工 curl 调用。

现有商品写接口使用 API key 和 `products:write` scope，适合脚本和内部集成；后台管理台需要账号登录体验和独立权限边界，因此不直接把管理员身份混入现有 API key 体系。

## 方案

第一版建设内部商品管理台，不建设完整公网后台产品。

后台前端作为项目内独立 Web 工程 `admin-web/`，使用 Vite、React、TypeScript 和轻量 CSS。开发时通过 Vite dev server 联调 API；生产构建后由 FastAPI 挂载到 `/admin`，前端路由 fallback 到 `index.html`，API 仍使用 `/api/v1/admin/...`。

后端新增管理员账号体系和独立 admin API namespace：

- `POST /api/v1/admin/auth/login`：用户名和密码登录，返回 8 小时 JWT access token。
- `GET /api/v1/admin/products`：后台商品列表。
- `GET /api/v1/admin/products/{product_id}`：后台商品详情。
- `POST /api/v1/admin/products`：创建商品。
- `PATCH /api/v1/admin/products/{product_id}`：更新商品。
- `DELETE /api/v1/admin/products/{product_id}`：软下架商品。
- `POST /api/v1/admin/upload`：管理员图片上传，复用现有上传 service。

管理员账号使用自建最小身份模型：

- 新增 `admin_users` 表。
- 密码使用 bcrypt 或同等级方案哈希存储。
- 第一版只支持 `role=admin`。
- 不开放注册页、找回密码、MFA、验证码、账号锁定、refresh token 或复杂 RBAC。
- 首个管理员通过 `python -m app.scripts.create_admin_user` 创建或重置。
- 生产环境必须配置 `ADMIN_JWT_SECRET`，不得使用占位值。

商品管理第一版只覆盖商品数据：

- 商品列表、搜索、筛选、分页。
- 商品创建、编辑、软下架。
- 基础结构化字段：`name`、`category`、`brand`、`sku`、`price`、`original_price`、`stock`、`stock_status`、`platform`、`product_url`、`image_url`、`rating`、`sales`、`description`、`review_summary`。
- 数组字段：`tags`、`suitable_scene`、`image_urls`。
- 高级 JSON 字段：`specs`、`feedback_metrics`，前端保存前校验 JSON。
- 图片上传成功后可设置为主图 `image_url` 或追加到 `image_urls`。

商品保存继续复用 `ProductService`。保存后商品索引同步仍为 best-effort，后台响应和前端提示只表达“已尝试同步索引”，第一版不做索引任务管理、重试队列或索引健康 dashboard。

## 影响

- API 路由：新增 `app/api/v1/admin/` 并在 `app/api/router.py` 注册。
- 鉴权：新增管理员登录、JWT 签发和 `require_admin` 依赖；保留现有 API key provider 供脚本和集成使用。
- 配置：新增 `ADMIN_JWT_SECRET`、`ADMIN_JWT_EXPIRE_MINUTES`。
- Model：新增 `app/models/admin_user.py`。
- Repository/Service：新增管理员用户持久化和认证 service；商品管理复用现有 `ProductService`。
- Migration：新增 `admin_users` 表迁移。
- Script：新增 `app/scripts/create_admin_user.py`。
- Frontend：新增 `admin-web/`。
- Static hosting：FastAPI 挂载 `admin-web/dist` 到 `/admin`。
- Docs：更新配置、API 或前端接入说明中与后台管理台相关的条目。

## 验证

- 后端测试覆盖管理员登录成功、密码错误统一失败、缺 JWT 访问 admin API 返回 401、无效 JWT 返回 401、有效 JWT 可创建/更新/下架商品。
- 后端测试覆盖创建管理员脚本的创建和显式重置行为。
- 上传测试覆盖 admin JWT 可上传、缺 JWT 被拒绝。
- 前端构建通过 `npm run build`。
- 后端验证运行相关 pytest；改动 docs 后运行 `python scripts/validate_docs.py`。
- 提交前运行 `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`。

## 最近检查

2026-05-26
