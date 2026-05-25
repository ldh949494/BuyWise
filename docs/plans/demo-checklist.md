# 演示检查清单

Status: Draft

## 启动前

- [ ] `.env` 已配置 `LLM_PROVIDER=openai-compatible`。
- [ ] `.env` 已配置有效的 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`。
- [ ] 非 mock 视觉或语音 provider 演示时，`.env` 已配置 `UPLOAD_PUBLIC_BASE_URL`，或 `UPLOAD_PROVIDER=cos`。
- [ ] 执行一键演示启动：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_demo.ps1
```

- [ ] 后端 Swagger 可打开：`http://127.0.0.1:8000/docs`。
- [ ] 另开终端执行备用 API 检查：

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_api_check.py --base-url http://127.0.0.1:8000
```

## Android 主路径

- [ ] Android 模拟器网络指向 `http://10.0.2.2:8000`。
- [ ] 首页能加载后端商品列表。
- [ ] 商品详情能从后端刷新。
- [ ] 商品详情点击“记录购买”后能显示模拟收货状态。
- [ ] 首页能显示收货后的待评价提示，并可一键提交固定内容评价。
- [ ] 对比页能展示至少两件商品的对比结果。
- [ ] 识图页点击“运行识图联调”能通过固定图片调用后端上传和识图接口。
- [ ] 识图页点击“运行语音联调”能通过固定音频调用后端上传和语音接口。
- [ ] AI 导购页发送演示问题：

```text
帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高
```

- [ ] AI 导购页能流式展示回复和商品卡片。
- [ ] 首推商品是 `Campus75 三模静音机械键盘`。

## Swagger 备用路径

- [ ] `GET /api/v1/health` 返回 `status=ok`。
- [ ] `GET /api/v1/products?page=1&page_size=5` 返回 demo 商品。
- [ ] `POST /api/v1/products/compare` 返回对比结果。
- [ ] `POST /api/v1/ai/chat` 使用演示问题返回结构化需求、回复和商品卡片。
- [ ] `POST /api/v1/orders` 记录模拟购买，连续调用 `POST /api/v1/orders/{order_id}/advance` 可推进到收货。
- [ ] `GET /api/v1/feedback/prompts` 返回已到期待评价项，`POST /api/v1/reviews/from-order-item` 可提交已购评价。

## 失败兜底

- [ ] Android 不可用时，切到 Swagger 或 `scripts/demo_api_check.py`。
- [ ] 向量索引构建失败时，说明后端会回退数据库候选，再使用 `-SkipIndex` 启动演示。
- [ ] 非 mock 多模态 provider 因相对媒体 URL 失败时，补充 `UPLOAD_PUBLIC_BASE_URL` 或切换 `UPLOAD_PROVIDER=cos`。
- [ ] LLM provider 不可用时，说明意图抽取会回退规则抽取，但真实导购回复依赖 LLM，需要恢复网关或 key。
- [ ] 端口被占用时，使用 `-Port 8123` 启动，并把备用检查 `--base-url` 同步改为该端口。

## 演示后

- [ ] 单独刷新并清理 `docs/entropy/baseline.json`，不要混入演示闭环提交。
- [ ] 需要提交时，运行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall
```
