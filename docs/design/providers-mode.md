# 设计：Provider 模式

Status: Implemented

## 背景

当认证、遥测、日志或错误处理在功能模块中被直接导入时，agent 容易意外创建多套实现。

## 方案

通过 `app.core.providers` 暴露横切能力。应用代码按名称获取 provider，例如 `get_provider("auth")`，而不是直接导入具体实现模块。

## 影响

后端应用工厂使用 logging、telemetry 和 error provider。本地验证通过 `scripts/auto_validate.ps1` 执行 provider 校验。

## 验证

运行 `python scripts/validate_providers.py`、`python scripts/validate_docs.py` 和 Python 测试套件。

## 最近检查

2026-05-15
