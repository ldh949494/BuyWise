# 设计：同步数据库阻塞边界

Status: Approved

## 背景

BuyWise 当前使用同步 SQLAlchemy session。FastAPI 路由中既有普通同步 endpoint，也有 async endpoint；如果 async 链路直接执行同步数据库查询，会占用事件循环或依赖隐式线程池行为，容量模型不清晰。

## 方案

当前版本保留同步 SQLAlchemy，不立即迁移 async SQLAlchemy。边界规则如下：

- Repository 和 service 继续使用同步 `Session`，不在 repository 内创建 async API。
- 同步 FastAPI endpoint 可以直接调用同步 service。
- async endpoint 中的高成本同步 DB 或向量检索路径必须通过 `app.core.concurrency.run_blocking_io` 包装。
- RAG pipeline 已通过 `search_products` 把同步检索代理到 blocking IO 执行；新增 async route 不得绕过该入口调用 `search_products_sync`。
- 数据库连接池由 SQLAlchemy engine 管理；生产环境优先通过 MySQL server/session 配置控制 statement timeout，避免单请求长期占用连接。
- 对需要强一致事务的写入路径，使用 `app.core.transaction.unit_of_work`，不在 async helper 内拆分事务提交。

## 容量约束

- DB 连接池大小必须小于 MySQL 可用连接数，并为迁移、readiness 和运维脚本保留余量。
- blocking IO 线程池并发不应高于 DB pool 可承载连接数，否则请求会在线程中等待连接并放大延迟。
- RAG、LLM、vision、speech 等高成本路径应同时受并发控制和 provider timeout 约束。

## 迁移路径

短期：

- 保持同步 SQLAlchemy。
- 为新 async endpoint 增加 code review 检查：禁止直接调用同步 DB service 的长耗时方法。
- 在压测或 closed beta 后根据 chat p95、DB pool wait、RAG latency 决定是否收敛更多入口到 blocking helper。

中期：

- 如果 DB wait 或线程池等待成为瓶颈，优先把查询密集的 RAG/readiness 路径拆成显式 blocking adapter。
- 增加 MySQL integration smoke，验证连接池、迁移、readiness 和索引检查在真实 MySQL 上的行为。

长期：

- 只有当同步边界和线程池调优仍无法满足容量目标时，再评估 async SQLAlchemy 迁移。
- async 迁移必须按 repository 分批，不混用同一事务内的 sync/async session。

## 影响

- `app.core.concurrency`：继续作为 async 链路调用同步阻塞工作的唯一 helper。
- `app.ai.rag_pipeline`：保持 async wrapper 和 sync implementation 分离。
- `app.core.database`：保留同步 `SessionLocal`；生产 statement timeout 通过 MySQL 配置或连接参数评估。
- `docs/conventions/backend.md`：后续可补充 code review 规则。

## 验证

- async RAG pipeline 测试应覆盖 `search_products`，而不是只测 `search_products_sync`。
- release 观察 chat p95、RAG latency、RAG fallback/empty rate 和 DB 连接错误。
- MySQL integration smoke 完成后，应覆盖连接、迁移、readiness 和索引检查。

## 最近检查

2026-05-31
