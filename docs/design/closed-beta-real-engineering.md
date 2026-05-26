# 设计：Closed Beta 真实工程落地

Status: Draft

## 背景

BuyWise 当前已具备 FastAPI 后端、Android 客户端、商品维护、RAG、对比、多模态接口、订单反馈闭环和可观测基础。但现有闭环仍偏演示：订单和反馈接口允许无 token 使用 `DEMO_USER_REF`，商品数据可来自 demo seed，Android 反馈是固定内容一键提交，购买状态是模拟推进。

Closed beta 的目标是进入受控真实试点，而不是公网生产或真实交易平台。系统需要使用真实商品目录、真实 AI provider、真实 Android 连接环境和受控用户身份，验证导购、对比、外部购买记录和购买后反馈是否能形成稳定闭环。

## 方案

Closed beta 运行模式使用 `APP_ENV=prod`，不新增 `APP_ENV=beta`。beta 作为部署环境名、数据库名、域名、Android 构建配置和 secret group 管理；后端继续触发生产配置校验，确保关闭 debug、使用显式 CORS、真实 secret、真实 MySQL、真实 LLM 和公网可访问媒体 URL。

用户身份第一阶段采用受控 API key，不建设完整账号登录系统。后端继续通过 `app.core.providers` 暴露 principal，但订单、待评价和评价接口在 prod 模式下必须携带 Bearer token，并引入明确 scope，例如 `orders:read`、`orders:write`、`feedback:read`、`feedback:write`。Android closed beta 构建通过配置注入 `BUYWISE_BETA_TOKEN`，repository 统一给需要身份的请求添加 Authorization。token 缺失时，Android 禁用记录购买、待评价、提交评价和上传联调等需要身份或权限的能力。

商品数据第一阶段使用人工维护的真实商品 CSV，不接爬虫或电商平台 API。CSV 继续以 `sku` 作为稳定业务键，必须包含真实 `product_url`、可展示图片、价格、类目、标签、场景和库存状态。发布准备流程使用 `release_prepare.ps1 -ImportCsv <path> -RequireRealCatalog -BuildIndex -IndexMode rebuild -CheckIndex`，不混用 demo seed 和 beta catalog。

购买闭环不接真实支付、库存扣减、物流履约、退款售后或平台订单验真。用户在外部电商平台购买后，在 BuyWise 记录外部购买。`external_platform` 在 closed beta 应作为必填业务字段，`external_order_ref` 可选但推荐填写。普通 Android 用户不直接使用 demo 状态推进接口；外部购买记录可由服务端按 closed beta 规则自动进入可反馈状态，或仅由具备管理/demo scope 的流程推进。

购买后反馈必须区分购买证据等级，不能把用户声明的外部购买称为平台验证购买。现有 `verified_purchase` 保留用于兼容，closed beta 使用 `purchase_evidence` 表达证据等级：`claimed`、`buywise_recorded`、`platform_verified`。推荐、对比和商品反馈权重按 evidence level 计算。Android 和 API 文案使用“已购反馈”或“购买后反馈”，不展示“验证购买”。

AI provider 第一阶段优先真实化文本导购、embedding 和识图。`LLM_PROVIDER` 使用 `openai` 或 `openai-compatible`，`EMBEDDING_PROVIDER` 使用 `openai-compatible` 或 `dashscope`，`VISION_PROVIDER` 使用 `llm` 或 `dashscope`。`EMBEDDING_BASE_URL` 和 `EMBEDDING_API_KEY` 可单独配置，默认复用 LLM provider 配置。`SPEECH_PROVIDER` 默认保持 `mock`，语音作为可选实验能力，等腾讯 ASR、公网音频 URL、成本、失败率和隐私提示都明确后再开启。AI 调用失败时，系统应保留规则抽取、RAG fallback 和可读错误文案，避免 Android 白屏。

部署第一阶段使用单机 Docker Compose、COS 和 HTTPS 反向代理。后端、MySQL、Prometheus、Loki、Promtail 和 Grafana 可在同一受控云主机上运行；上传长期存储走 COS；Chroma 使用本地持久化目录，closed beta 只运行单副本。后续再评估托管 MySQL、独立向量库和容器平台。

最低运维门槛是可定位、可恢复、可回滚。必须保留后端 JSON 日志、request id、Prometheus metrics、Loki 日志、Grafana 查询入口、MySQL 每日备份、发布前备份、CSV 加索引重建恢复路径、COS 生命周期配置和上一版镜像/tag 回滚路径。Closed beta 需要 readiness 检查或脚本，至少覆盖 MySQL 可连、Chroma collection 可读、商品数大于 0 和索引健康。

## 非目标

- 不做公网开放注册、手机号登录、OAuth/OIDC 登录或 token refresh。
- 不接支付、真实库存扣减、物流履约、售后、退款或平台订单验真。
- 不接爬虫或电商平台实时 API。
- 不做多副本部署、自动扩缩容、多区域高可用或复杂告警路由。
- 不默认开启真实语音识别。

## 影响

- 后端配置：prod 模式保留，增加 closed beta scope、token 和购买证据相关配置说明。
- 后端 API：订单、待评价和评价接口在 prod 模式下从可选身份迁移到强身份；购买记录语义从模拟购买调整为外部购买记录。
- 后端模型和 schema：需要引入购买证据等级，或以兼容字段表达 claimed/recorded/platform_verified。
- 后端服务：反馈权重按购买证据等级计算，外部购买记录不再宣称平台验真。
- Android：增加 beta token 配置、统一 Authorization 注入、记录外部购买表单、完整反馈表单、待评价错误状态和反馈摘要展示。
- 数据发布：定义 beta catalog CSV 和导入、索引重建、索引检查流程。
- 部署运维：补充 closed beta compose/env、HTTPS 反代、readiness、备份恢复和回滚 runbook。
- 文档：同步 `docs/reference/api.md`、`docs/reference/configuration.md`、`docs/reference/scripts.md`、Android 边界、运行时与可观测性文档。

## 验证

- 后端测试覆盖 prod 模式下订单、待评价和评价接口缺 token 返回 401，缺 scope 返回 403，有效 token 使用 token subject 作为 `user_ref`。
- API 测试覆盖外部购买记录创建、购买证据等级、待评价、提交反馈、更新和撤回。
- 服务测试覆盖 feedback 权重按 evidence level 计算，claimed/recorded 低于未来 platform_verified。
- Android 构建验证 beta base URL 和 token 注入，缺 token 时相关入口禁用。
- 商品导入测试覆盖 beta CSV 必填字段、真实 URL 字段和不混用 seed profile。
- 发布验证运行迁移、CSV 导入、向量索引 rebuild/check、readiness 脚本和核心 API smoke。
- 文档修改后运行 `python scripts/validate_docs.py`。

## 最近检查

2026-05-25
