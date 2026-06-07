# 设计：P2 多模态演示路径

Status: Implemented

## 背景

BuyWise 已有上传、视觉识别和语音识别后端接口。P2 目标是跑通后端联调闭环，并明确真实 provider 的演示配置。后续实现已补齐 Android 相册、拍照和麦克风录音输入。

## 方案

视觉真实 provider 固定为 OpenAI-compatible 多模态接口，演示优先使用 DashScope/Qwen-VL 兼容服务。语音真实 provider 固定为上传音频后的 URL ASR，演示使用腾讯 ASR `SentenceRecognitionRequest.Url` 路径，不做二进制直传。

当 `APP_ENV=prod` 且视觉或语音 provider 非 mock 时，必须配置 `UPLOAD_PUBLIC_BASE_URL` 或使用 `UPLOAD_PROVIDER=cos`。演示启动脚本同样在非 mock 多模态 provider 下做前置检查；普通 dev 保留请求级 `media_url_not_public` 错误。

上传生命周期 P2 只做本地 TTL 清理脚本，COS 生命周期通过部署文档要求配置。Android 可用相册/拍照图片和 m4a 录音触发 upload -> vision/asr -> UI 展示或导购填充。

## 影响

- `app/core/config.py`：增加非 mock 多模态 provider 的生产配置校验。
- `scripts/start_demo.ps1`：增加演示启动前 `UPLOAD_PUBLIC_BASE_URL` 检查。
- `app/scripts/cleanup_uploads.py`：清理本地上传目录的过期文件。
- Android `ShopRepository`、`BuyWiseViewModel`、`VisionScreen`：增加固定资源后端联调按钮和状态。
- 文档同步真实 provider、上传清理和 Android 演示限制。

## 验证

- 后端测试覆盖配置校验和 cleanup dry-run/delete。
- Android analyze 验证固定资源联调代码编译通过。
- `auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild` 验证后端主门禁。

## 剩余边界/后续工作

- Android 已支持相册、拍照和麦克风录音输入；真实语音识别仍依赖公网可访问音频 URL。
- 真实 provider 需要公网可访问媒体 URL；`APP_ENV=prod` 且非 mock 多模态 provider 时，必须配置 `UPLOAD_PUBLIC_BASE_URL` 或使用 `UPLOAD_PROVIDER=cos`。
- COS 上传生命周期不由应用脚本管理，生产环境应在 bucket 上配置生命周期规则。

## 最近检查

2026-05-25
