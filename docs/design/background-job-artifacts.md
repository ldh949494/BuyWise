# 设计：后台作业执行结果 Artifact

Status: Implemented

## 背景

BuyWise closed beta 发布准备依赖多条后台维护作业：商品导入、向量索引构建、COS 商品图片迁移、备份检查和发布准备聚合流程。现有 `app.scripts.job_artifacts.run_job_with_artifact` 已为 `import_products` 与 `build_vector_index` 提供机器可读执行记录，但 COS image migration、backup check 和 `release_prepare.ps1` 聚合结果仍依赖命令行输出或人工 checklist。

## 方案

后台作业继续复用统一 JSON artifact schema：作业名称、输入、输出、开始和结束时间、耗时、状态、错误、执行环境和操作者。

- `app.scripts.migrate_product_images_to_cos` 新增 `--artifact-json`，记录 dry-run/apply、limit 和 include-cos-urls 输入，输出现有迁移 summary。
- 新增 `app.scripts.check_mysql_backup`，校验指定 MySQL 备份文件存在、是文件、非空，并可选校验最小字节数和最大文件年龄；脚本不创建备份、不恢复备份。
- `scripts/release_prepare.ps1` 新增 `-ArtifactDir` 和 `-ArtifactJson`。开启 artifact 时，为 import/build-index 写入子 artifact，并输出 release_prepare 聚合 artifact，记录每个步骤的状态、输入、子 artifact 路径、输出和失败原因。
- Closed beta release checklist 必须引用 backup check artifact、release_prepare aggregate artifact 以及适用的 readiness、index、RAG、real dependency 和 smoke artifact。

## 影响

- 脚本：`app/scripts/migrate_product_images_to_cos.py`、`app/scripts/check_mysql_backup.py`、`scripts/release_prepare.ps1`。
- 测试：新增或更新后台作业 artifact、备份检查和 release prepare 脚本约束测试。
- 文档：`docs/operations/release-checklist.md`、`docs/operations/closed-beta-runbook.md`、`docs/reference/scripts.md`、`docs/plans/archive/backend-framework-hardening.md`。

## 验证

- Python 单元测试验证备份检查成功、失败和 artifact 输出。
- COS image migration 测试验证 CLI 支持 `--artifact-json` 并通过统一 helper 记录 summary。
- Release prepare 文本测试验证新 artifact 参数、子 artifact 传递和聚合写入函数存在。
- 文档校验确认 checklist 和脚本引用不漂移。

## 最近检查

2026-05-31
