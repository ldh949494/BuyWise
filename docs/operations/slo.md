# BuyWise Closed Beta SLO

Use these SLOs as release and operations decision thresholds for the closed beta backend. They are not hard product promises; they define when a release needs investigation, rollback, or a documented exception.

## Metrics

| Signal | Target | Source |
| --- | --- | --- |
| Chat p95 latency | `<= 5s` for `/api/v1/ai/chat` and stream first useful response | metrics and request logs |
| RAG empty result rate | `<= 2%` over the release window | `buywise_rag_empty_results_total` and RAG eval gate |
| RAG fallback rate | `<= 15%` over the release window | `buywise_rag_fallback_total` and RAG eval gate |
| LLM degraded rate | `<= 5%` for AI chat sessions | chat response `extra.degraded` and logs |
| Upload failure rate | `<= 1%` for upload attempts | upload route status and logs |
| Feedback submit failure rate | `<= 1%` for review submission attempts | review route status and logs |
| Order to feedback conversion | `>= 30%` for closed beta testers after the review prompt window | order and review records |

## Release Record

Every release record should include:

- Current release SLO snapshot and previous release snapshot.
- Absolute value and delta for every metric above.
- RAG eval gate JSON artifact when `-RunRagEval` is used.
- Readiness, smoke, index health, and OpenAPI contract results.
- Any exception owner, reason, expected impact, and follow-up date.

## Actions

- If one quality metric misses target but smoke passes, release can continue only with a written exception.
- If readiness, smoke, OpenAPI contract, or RAG eval gate fails, block the release.
- If chat p95, LLM degraded rate, upload failure rate, or feedback submit failure rate worsens by more than 50% from the previous release, investigate before widening beta access.

## Recently Checked

2026-05-31
