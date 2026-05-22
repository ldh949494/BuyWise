# 设计：P2 多模态演示路径

Status: Draft

## 背景

BuyWise 已有上传、视觉识别和语音识别后端接口，但 Android 识图页仍是本地演示。P2 目标是跑通后端联调闭环，并明确真实 provider 的演示配置，不建设完整相机、相册或录音采集能力。

## 方案

视觉真实 provider 固定为 OpenAI-compatible 多模态接口，演示优先使用 DashScope/Qwen-VL 兼容服务。语音真实 provider 固定为上传音频后的 URL ASR，演示使用腾讯 ASR `SentenceRecognitionRequest.Url` 路径，不做二进制直传。

当 `APP_ENV=prod` 且视觉或语音 provider 非 mock 时，必须配置 `UPLOAD_PUBLIC_BASE_URL` 或使用 `UPLOAD_PROVIDER=cos`。演示启动脚本同样在非 mock 多模态 provider 下做前置检查；普通 dev 保留请求级 `media_url_not_public` 错误。

上传生命周期 P2 只做本地 TTL 清理脚本，COS 生命周期通过部署文档要求配置。Android P2 用固定演示图片和音频 bytes 触发 upload -> vision/asr -> UI 展示或导购填充，不做系统相机、相册、麦克风权限和转码。

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

## 最近检查

2026-05-22
