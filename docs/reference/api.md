# API Reference Notes

The backend registers public routes under `/api/v1` by default.

## Route Groups

- Health: `/api/v1/health`
- Products: `/api/v1/products`
- Product compare: `/api/v1/products/compare`
- AI chat: `/api/v1/ai/chat`
- RAG search: `/api/v1/rag/search`
- Upload: `/api/v1/upload`
- Vision: `/api/v1/vision/recognize`
- Speech: `/api/v1/speech/asr`

## Generated Reference

Run the backend and open `/docs` for the OpenAPI UI. Browser validation can capture the docs page with `scripts/browser_check.py`.

## Response Notes

- Product responses include optional extended commerce fields: `sku`, `product_url`, `image_urls`, `stock_status`, `review_summary`, and `price_history`.
- Chat responses include `extra.session_id` for the persisted chat session.
- Chat product cards include explanation fields: `budget_match`, `scenario_match`, `conflicts`, and `alternatives`.

## Authentication Notes

- `POST /api/v1/upload` requires `Authorization: Bearer <token>` with the `upload:write` scope.
- `POST /api/v1/products` requires `Authorization: Bearer <token>` with the `products:write` scope.
- Product browse/detail, compare, and AI chat remain public for the current Android integration flow.
- Auth, request context, errors, telemetry, and logging must be accessed through `app.core.providers`; `scripts/validate_providers.py` blocks direct imports from provider implementation modules.

| Flow | Method | Path | Principal | Required Scope |
| --- | --- | --- | --- | --- |
| Health | `GET` | `/api/v1/health` | Public | None |
| Product browse | `GET` | `/api/v1/products` | Public | None |
| Product detail | `GET` | `/api/v1/products/{product_id}` | Public | None |
| Product create | `POST` | `/api/v1/products` | Bearer token | `products:write` |
| Product compare | `POST` | `/api/v1/products/compare` | Public | None |
| AI guide | `POST` | `/api/v1/ai/chat` | Public | None |
| RAG search | `POST` | `/api/v1/rag/search` | Public | None |
| Upload | `POST` | `/api/v1/upload` | Bearer token | `upload:write` |
| Vision recognize | `POST` | `/api/v1/vision/recognize` | Public | None |
| Speech ASR | `POST` | `/api/v1/speech/asr` | Public | None |

## Android Contract Flows

The native Android client should depend on these three backend flows first:

- Product browse: `GET /api/v1/products` for category, keyword, price, and pagination filters; `GET /api/v1/products/{product_id}` for detail.
- Product compare: `POST /api/v1/products/compare` with `product_ids` and optional `user_need`.
- AI guide: `POST /api/v1/ai/chat` with `session_id` and `message`, optionally `image_url` and `audio_url`.

`app.scripts.seed_products.seed_android_contract_products` provides deterministic product data for these flows. `tests/test_android_contract_api.py` locks the response shapes used by Android so future real AI provider work can change ranking and prose without removing required fields.

## RAG Quality Loop

RAG retrieval quality is tracked with `data/rag_eval/shopping_needs.jsonl`. Run `python -m app.scripts.evaluate_rag` to inspect `recall@k`, `top1_accuracy`, `mrr@k`, and current failure cases. `tests/test_rag_eval.py` keeps a light regression gate over the fixed evaluation set.
