# 设计：P1 商品数据能力

Status: Implemented

## 背景

BuyWise 需要补齐内部商品维护闭环，让演示和调试数据可以稳定创建、更新、下架、导入和重新索引。P1 不建设完整后台管理产品，只覆盖受保护 API 与脚本级维护能力。

## 方案

商品删除采用软下架：保留商品、价格历史、评论和历史推荐引用，默认列表、详情、RAG、推荐和对比不返回下架商品。创建、更新和下架在 DB 写入成功后 best-effort upsert 向量索引；索引失败只记录结构化日志，不回滚 DB。

CSV 导入按 `sku` 作为幂等键，整批校验失败。必填字段为 `sku`、`name`、`category`、`price`、`tags`；`price` 必须非负，`tags` 必须是非空 JSON list，同一 CSV 内重复 sku 直接失败。

`price_history`、`review_summary` 和已购反馈聚合指标进入商品读取响应，用于 Android 合同流、商品详情、推荐解释和对比分析。商品维护入口包括受保护 API 和 CLI 脚本复用 service，不做 Web 管理后台、审批流或复杂权限。

## 影响

- `app/api/v1/products.py`：新增 update 与软下架接口。
- `app/services/product_service.py`：集中商品维护、默认过滤下架、best-effort 索引。
- `app/repositories/product_repo.py`：支持 update、按 sku upsert、活跃商品过滤。
- `app/scripts/import_products.py`：整批校验并按 sku upsert。
- `app/services/recommend_service.py` 与 `app/services/compare_service.py`：接入价格历史和评论摘要评分。

## 验证

- API 测试覆盖 update/delete 权限、软下架过滤和索引失败不回滚。
- CSV 测试覆盖 sku upsert、必填校验和整批失败。
- 推荐/对比测试覆盖价格历史和评论对排序及理由的影响。
- 运行 `powershell.exe -ExecutionPolicy Bypass -File .\scripts\auto_validate.ps1 -SkipDependencyInstall -SkipAndroidBuild`。

## 剩余边界/后续工作

- 不建设完整 Web 管理后台、审批流或复杂权限；商品维护仍限定为受保护 API 和脚本。
- 向量索引写入仍是 best-effort，索引失败不回滚 DB；需要通过索引健康检查和重建脚本兜底。
- 价格历史和评论聚合已进入公开读取响应，后续新增字段时应继续同步 `docs/reference/api.md` 和 Android 合同测试。

## 最近检查

2026-05-25
