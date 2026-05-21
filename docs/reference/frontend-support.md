# 前端接入支持指南

本文档面向 BuyWise 前端接入当前 FastAPI 后端框架，覆盖环境、接口契约、鉴权、错误处理和联调注意事项。

## 后端基线

- 默认服务地址：`http://localhost:8000`
- 默认 API 前缀：`/api/v1`
- OpenAPI 文档：`/docs`
- OpenAPI JSON：`/openapi.json`
- 健康检查：`GET /api/v1/health`
- Android 模拟器访问宿主机时使用：`http://10.0.2.2:8000`

后端通过 `CORS_ALLOWED_ORIGINS` 控制跨域，当前默认允许：

- `http://localhost:3000`
- `http://localhost:5173`
- `http://10.0.2.2:8000`

如果 Web 前端使用其他端口，需要后端同步加入 CORS 白名单。

## 请求约定

- JSON 请求使用 `Content-Type: application/json`。
- 文件上传使用 `multipart/form-data`，字段名固定为 `file`。
- 建议所有请求带 `X-Request-ID`，便于联调日志定位。
- 当前公开浏览、对比、AI 导购、RAG、视觉识别、语音识别接口不要求登录。
- `POST /api/v1/upload` 和 `POST /api/v1/products` 需要 Bearer Token。

鉴权头格式：

```http
Authorization: Bearer <token>
```

## 错误结构

后端统一错误响应格式：

```json
{
  "detail": "Request validation failed",
  "code": "validation_error",
  "extra": {
    "request_id": "optional-request-id",
    "errors": []
  }
}
```

前端建议：

- 优先展示 `detail`。
- 使用 `code` 做分支处理。
- 将 `extra.request_id` 展示在错误详情或上报日志中。

常见状态码：

| 状态码 | 错误码 | 场景 |
| --- | --- | --- |
| `400` | `invalid_upload_filename` / `unsafe_upload_path` | 上传文件名非法或路径不安全 |
| `401` | `unauthorized` | 缺少或无效 Bearer Token |
| `403` | `forbidden` | Token 权限不足 |
| `404` | `not_found` | 商品不存在 |
| `413` | `upload_too_large` | 请求体或上传文件过大 |
| `415` | `unsupported_upload_type` | 上传文件类型或扩展名不支持 |
| `422` | `validation_error` | 请求参数或 JSON 结构不符合 schema |
| `500` | `internal_error` | 未预期服务端错误 |

## 端点汇总

| 流程 | 方法 | 路径 | 鉴权 | 前端用途 |
| --- | --- | --- | --- | --- |
| 健康检查 | `GET` | `/api/v1/health` | 公开 | 启动页、联调探活 |
| 商品浏览 | `GET` | `/api/v1/products` | 公开 | 商品列表、搜索、筛选 |
| 商品详情 | `GET` | `/api/v1/products/{product_id}` | 公开 | 商品详情页 |
| 商品创建 | `POST` | `/api/v1/products` | `products:write` | 后台录入或测试数据创建 |
| 商品对比 | `POST` | `/api/v1/products/compare` | 公开 | 商品对比页 |
| AI 导购 | `POST` | `/api/v1/ai/chat` | 公开 | AI 导购会话 |
| RAG 搜索 | `POST` | `/api/v1/rag/search` | 公开 | 检索调试或推荐候选 |
| 上传 | `POST` | `/api/v1/upload` | `upload:write` | 图片、音频上传 |
| 视觉识别 | `POST` | `/api/v1/vision/recognize` | 公开 | 图片识别后生成搜索 query |
| 语音识别 | `POST` | `/api/v1/speech/asr` | 公开 | 语音转文字后进入导购 |

## 商品浏览

```http
GET /api/v1/products?category=机械键盘&keyword=静音&page=1&page_size=20
```

Query 参数：

| 名称 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `category` | string | 否 | 类目筛选 |
| `keyword` | string | 否 | 关键词搜索 |
| `price_min` | number | 否 | 最低价，必须 `>= 0` |
| `price_max` | number | 否 | 最高价，必须 `>= 0` |
| `page` | integer | 否 | 默认 `1`，必须 `>= 1` |
| `page_size` | integer | 否 | 默认 `20`，范围 `1..100` |

响应：

```json
{
  "items": [
    {
      "id": 1001,
      "name": "K87 静音红轴机械键盘",
      "category": "机械键盘",
      "brand": "KeyNova",
      "sku": "android-keyboard-k87",
      "price": 269.0,
      "original_price": 329.0,
      "platform": "BuyWise",
      "product_url": "https://example.com/products/android-keyboard-k87",
      "image_url": "https://example.com/images/android-keyboard-k87.jpg",
      "image_urls": [],
      "rating": 4.8,
      "sales": 1200,
      "description": "适合宿舍写代码的静音键盘",
      "specs": {"layout": "87键", "switch": "静音红轴"},
      "tags": ["静音", "机械键盘"],
      "suitable_scene": ["宿舍", "办公"],
      "stock": 20,
      "stock_status": "in_stock",
      "review_summary": "用户反馈按键安静、手感稳定",
      "created_at": "2026-05-19T10:00:00",
      "price_history": [{"date": "2026-05-01", "price": 299.0}]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

前端展示建议：

- 列表卡片优先使用 `image_url`，详情页可使用 `image_urls` 做轮播。
- `price`、`rating`、`stock_status` 都是可空字段，需要兜底。
- `specs` 可能是对象、数组或空值，详情页应做动态渲染。

## 商品详情

```http
GET /api/v1/products/1001
```

响应结构与 `ProductRead` 一致。商品不存在时返回 `404`。

## 商品对比

```http
POST /api/v1/products/compare
Content-Type: application/json

{
  "product_ids": [1001, 1002],
  "user_need": "宿舍使用，安静，预算300以内",
  "session_id": "optional-session-id"
}
```

响应：

```json
{
  "items": [
    {
      "id": 1001,
      "product_id": 1001,
      "name": "K87 静音红轴机械键盘",
      "price": 269.0,
      "image_url": "https://example.com/images/android-keyboard-k87.jpg",
      "rating": 4.8,
      "score": 92.0,
      "pros": ["安静", "价格合适", "适合宿舍"],
      "cons": ["不支持无线"],
      "specs": {"layout": "87键"}
    }
  ],
  "summary": "更推荐 K87，原因是预算匹配且噪音低。",
  "winner_id": 1001
}
```

前端展示建议：

- 用 `winner_id` 高亮推荐项。
- 对比项的 `id` 和 `product_id` 当前通常一致，但渲染跳转商品详情时优先使用 `product_id`，为空时回退到 `id`。
- `pros`、`cons` 为空时隐藏对应区域。

## AI 导购聊天

```http
POST /api/v1/ai/chat
Content-Type: application/json

{
  "session_id": "web-session-001",
  "message": "推荐一个宿舍写代码用的机械键盘，预算300以内，声音小一点",
  "image_url": "/uploads/example.png",
  "audio_url": "/uploads/example.wav"
}
```

`message`、`image_url`、`audio_url` 都是可选字段，但前端至少应提交一种用户输入。

响应：

```json
{
  "reply": "可以优先看静音红轴、87键布局的键盘。",
  "need_clarify": false,
  "structured_need": {
    "intent": "商品推荐",
    "category": "机械键盘",
    "budget_max": 300,
    "scenario": "宿舍",
    "preferences": ["低噪音"],
    "avoid": [],
    "need_clarify": false,
    "missing_fields": []
  },
  "products": [
    {
      "id": 1001,
      "name": "K87 静音红轴机械键盘",
      "price": 269.0,
      "image_url": "https://example.com/images/android-keyboard-k87.jpg",
      "rating": 4.8,
      "score": 92.0,
      "tags": ["静音"],
      "reason": "预算匹配，适合宿舍环境。",
      "budget_match": true,
      "scenario_match": true,
      "conflicts": [],
      "alternatives": []
    }
  ],
  "extra": {
    "session_id": "web-session-001"
  }
}
```

前端展示建议：

- 使用 `extra.session_id` 作为后续会话 ID；如果前端首次没有传，后端可能生成或回传会话标识。
- `need_clarify=true` 时应把 `reply` 渲染为追问，不直接进入最终推荐态。
- `structured_need.missing_fields` 可用于展示缺失条件，如预算、用途、偏好。
- `products` 可作为聊天消息中的商品卡片。

## 上传

```http
POST /api/v1/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=<binary>
```

支持类型：

| 内容类型 | 扩展名 |
| --- | --- |
| `image/png` | `.png` |
| `image/jpeg` | `.jpg`, `.jpeg` |
| `image/webp` | `.webp` |
| `image/gif` | `.gif` |
| `audio/wav` | `.wav` |
| `audio/mpeg` | `.mp3` |
| `audio/mp4` | `.m4a` |
| `audio/ogg` | `.ogg` |

默认大小限制：`10MB`。

响应：

```json
{
  "url": "/uploads/9f7a1a4f5e164d5da0c4c6d8211f84be.png",
  "filename": "9f7a1a4f5e164d5da0c4c6d8211f84be.png"
}
```

注意：`UPLOAD_PROVIDER=local` 且未配置 `UPLOAD_PUBLIC_BASE_URL` 时返回后端相对 URL；启用 `UPLOAD_PUBLIC_BASE_URL` 或 `UPLOAD_PROVIDER=cos` 时返回外部可访问 URL。
当后端启用非 mock 视觉或语音 provider 时，应让上传接口返回可被外部模型或腾讯 ASR 访问的 URL。

## 视觉识别

```http
POST /api/v1/vision/recognize
Content-Type: application/json

{
  "image_url": "/uploads/example.png"
}
```

响应：

```json
{
  "category": "机械键盘",
  "features": ["白色", "无线", "紧凑布局"],
  "query": "白色 无线 紧凑布局 机械键盘"
}
```

前端可将 `query` 自动填入搜索框，或转发给 `/api/v1/ai/chat` 继续导购。

## 语音识别

```http
POST /api/v1/speech/asr
Content-Type: application/json

{
  "audio_url": "/uploads/example.wav"
}
```

响应：

```json
{
  "text": "我想买一个宿舍用的机械键盘，预算三百以内"
}
```

前端可将 `text` 放入输入框供用户确认，或直接发送给 `/api/v1/ai/chat`。

## RAG 搜索

```http
POST /api/v1/rag/search
Content-Type: application/json

{
  "query": "宿舍 静音 机械键盘 300以内",
  "top_k": 5,
  "filters": {
    "category": "机械键盘"
  }
}
```

响应：

```json
{
  "query": "宿舍 静音 机械键盘 300以内",
  "items": [],
  "total": 0
}
```

`items` 当前是开放字典数组，前端不要假设强类型字段稳定；生产页面优先使用 `/products`、`/products/compare` 和 `/ai/chat`。

## 前端接入优先级

建议优先接入以下主链路：

1. 商品列表和详情：`GET /products`、`GET /products/{id}`。
2. 商品对比：`POST /products/compare`。
3. AI 导购：`POST /ai/chat`，渲染 `reply`、`structured_need`、`products`。
4. 多模态输入：上传后调用 `vision/recognize` 或 `speech/asr`，再进入搜索或 AI 导购。

## 本地验证

后端可用以下命令启动和验证：

```powershell
docker compose up --build
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

前端联调最小检查：

- `GET /api/v1/health` 返回 `{"status":"ok","service":"buywise-backend"}`。
- 商品列表能处理空列表和分页。
- 商品详情能处理 `404`。
- AI 导购能保持 `session_id`。
- 上传能正确处理 `401`、`413`、`415`。
- 错误提示中记录 `extra.request_id`。
