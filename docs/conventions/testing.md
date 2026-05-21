# 测试约定

## Python

- 测试放在 `tests/`。
- 测试文件使用 `test_*.py` 或 `*_test.py` 命名。
- 后端行为优先使用聚焦的 service 测试和 API contract 测试。
- FastAPI 应用测试使用 `create_app()`。

## 验证脚本

`scripts/auto_validate.ps1` 是本地提交前和 CI 的验证入口。它会安装依赖（除非跳过）、运行文档校验、provider lint、仓库 lint、熵债校验、后端 smoke check、pytest，并可选择构建 Android。

该脚本运行 pytest 时使用仓库内 `.pytest_tmp/auto-validate` 作为 basetemp，并禁用 pytest cache。完整验证优先使用该脚本，避免本机系统 Temp 或 cache 目录权限影响测试。

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild
```

聚焦调试时可以直接运行 pytest。全量本地运行时建议显式指定仓库内 basetemp：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_tmp\manual
```

## 文档

修改 `AGENTS.md`、`docs/`、指向 docs 的 README 说明或维护 docs 的脚本时，运行 `python scripts/validate_docs.py`。
