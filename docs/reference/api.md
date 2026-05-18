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
