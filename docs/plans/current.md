# 当前计划

## 目标

随着 BuyWise 演进，保持仓库记忆系统准确。

## 活跃任务

- [ ] 后端、Android、运行时或可观测边界变化时，更新架构文档。
- [ ] 公共端点、环境变量或脚本变化时，更新参考文档。
- [ ] 修改文档后运行 `python scripts/validate_docs.py`。
- [ ] 重大结构变化后运行 `python scripts/doc_gardening.py`。

## 验证

- `python scripts/validate_docs.py`
- `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`
