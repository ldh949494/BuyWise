# 黄金原则

主观代码品味必须转化为 CI 可执行的机械规则。

## 机械规则

- Python 函数不超过 30 行。
- 复用已有 helper，不复制实现。
- 公开 service 和 repository 函数应以动作动词开头。
- 宽泛异常处理必须通过 `ErrorProvider` 上报，或补充上下文后重新抛出。
- `TODO`、`FIXME`、`HACK` 注释必须包含 `owner:` 或 `issue:`。

## 修复模式

- 将过长编排拆成更小的私有 helper。
- 将共享纯 helper 移到 `app/utils/` 或拥有该行为的 service/repository。
- API 路由保持轻量，业务行为放在 service。
- 宽泛错误处理使用 `get_provider("errors")` 或 `get_error_provider()`。
- 真实工作项中的过期注释应转换为 `docs/plans/current.md` 任务。

熵债验证器会用 `ERROR`、`FIX` 和 `SEE` 输出每个问题，方便 agent 无需加载额外上下文即可处理。
