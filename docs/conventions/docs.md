# 文档约定

## 渐进披露

- `AGENTS.md` 保持短小，只作为入口地图链接到更深文档。
- 稳定架构放在 `docs/architecture/`。
- 功能决策放在 `docs/design/`。
- 编码和测试约定放在 `docs/conventions/`。
- 当前工作放在 `docs/plans/current.md`。
- 生成物或参考资料放在 `docs/reference/`。

## 状态字段

设计文档必须包含且只包含一个状态行，值必须是以下之一：

- `Status: Draft`
- `Status: Approved`
- `Status: Implemented`
- `Status: Deprecated`

该状态行需要保持英文格式，因为 `scripts/validate_docs.py` 会校验它。

## 维护

代码结构变化时，在同一变更中更新最接近的相关文档。不确定时运行 `python scripts/doc_gardening.py`，再人工审阅报告。

## 编码

- 文本文件保存为 UTF-8。
- 不提交 GBK/ANSI 文本，也不提交 UTF-8 中文被错误解码后的乱码。
- 通过仓库内 PowerShell 入口运行脚本；它们会加载 `scripts/set_utf8.ps1`，确保 Python 和控制台输出使用 UTF-8。
- `scripts/validate_repo_lint.py` 会拒绝非 UTF-8 文本文件和常见乱码标记。
