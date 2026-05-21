# 后台清理 Agent

后台清理 agent 会定期创建小范围的熵债清理 PR。

## 触发

- GitHub Actions workflow：`.github/workflows/entropy-cleanup-agent.yml`
- 计划任务：每周一次
- 手动触发：`workflow_dispatch`

## 安全规则

- 每次只清理一个选定的熵债问题。
- 不刷新 `docs/entropy/baseline.json`。
- 不自动合并。
- 创建普通 PR，并附带 review label。
- 创建 PR 前运行仓库验证。
- 拒绝超过 500 行变更的 diff。

## 允许范围

该 agent 只能编辑 `app/`、`tests/`、`docs/`、`scripts/`、`AGENTS.md` 或 `README.md`。

## 审查

每个生成的 PR 都必须包含行为保持、范围控制和验证结果清单。
