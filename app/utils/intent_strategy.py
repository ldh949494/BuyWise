"""Shared intent strategy helpers."""


def retrieval_strategy_for(intent: str, purchase_stage: str) -> str:
    if intent in {"bundle_recommend", "场景化组合推荐"}:
        return "bundle"
    if purchase_stage == "browse":
        return "explore"
    if purchase_stage == "buy_ready":
        return "strict"
    return "balanced"
