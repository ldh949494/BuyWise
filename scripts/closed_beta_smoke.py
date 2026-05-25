from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any
import urllib.error
import urllib.request


def main() -> None:
    args = _parse_args()
    result = run_smoke(
        base_url=args.base_url.rstrip("/"),
        token=args.token,
        readiness_token=args.readiness_token,
        include_ai=args.include_ai,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_smoke(base_url: str, token: str, readiness_token: str, include_ai: bool = False) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("smoke-%Y%m%d-%H%M%S")
    auth_headers = {"Authorization": f"Bearer {token}"}
    basics = _run_basic_checks(base_url, readiness_token)
    product_id = _first_product_id(basics["products"])
    order = _create_smoke_order(base_url, product_id, run_id, auth_headers)
    prompts = request_json("GET", f"{base_url}/api/v1/feedback/prompts", headers=auth_headers)
    review = _submit_smoke_review(base_url, _matching_prompt(prompts, order), run_id, auth_headers)
    ai = _run_ai_check(base_url) if include_ai else None
    _assert_smoke(basics, order, prompts, review, ai)
    return _smoke_summary(run_id, product_id, basics, order, review, ai)


def _run_basic_checks(base_url: str, readiness_token: str) -> dict[str, Any]:
    return {
        "health": request_json("GET", f"{base_url}/api/v1/health"),
        "ready": request_json("GET", f"{base_url}/api/v1/ready", headers={"X-Readiness-Token": readiness_token}),
        "products": request_json("GET", f"{base_url}/api/v1/products?page=1&page_size=5"),
        "rag": request_json("POST", f"{base_url}/api/v1/rag/search", {"query": "适合宿舍的安静键盘", "top_k": 3}),
    }


def _create_smoke_order(base_url: str, product_id: int, run_id: str, headers: dict[str, str]) -> dict[str, Any]:
    return request_json(
        "POST",
        f"{base_url}/api/v1/orders",
        {
            "product_id": product_id,
            "quantity": 1,
            "external_platform": "smoke",
            "external_order_ref": run_id,
        },
        headers=headers,
    )


def _submit_smoke_review(
    base_url: str,
    prompt: dict[str, Any],
    run_id: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    return request_json(
        "POST",
        f"{base_url}/api/v1/reviews/from-order-item",
        {
            "order_item_id": prompt["order_item_id"],
            "rating": 5,
            "content": f"{run_id} 发布验证反馈，商品体验符合预期",
            "usage_context": "closed_beta_smoke",
            "pros_tags": ["good_value"],
            "cons_tags": [],
            "met_expectation": True,
        },
        headers=headers,
    )


def _smoke_summary(
    run_id: str,
    product_id: int,
    basics: dict[str, Any],
    order: dict[str, Any],
    review: dict[str, Any],
    ai: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "health": basics["health"]["status"],
        "ready": basics["ready"]["status"],
        "product_id": product_id,
        "rag_total": basics["rag"]["total"],
        "order_id": order["id"],
        "review_id": review["id"],
        "ai": ai,
    }


def _run_ai_check(base_url: str) -> dict[str, Any]:
    chat = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": "closed-beta-smoke", "message": "推荐一款适合宿舍使用的低噪音键盘"},
    )
    return {
        "product_count": len(chat.get("products", [])),
        "degraded": bool(chat.get("extra", {}).get("degraded")),
    }


def _assert_smoke(*payloads: Any) -> None:
    basics, order, prompts, review, ai = payloads
    assert basics["health"]["status"] == "ok"
    assert basics["ready"]["status"] == "ready"
    assert basics["products"]["items"]
    assert basics["rag"]["items"]
    assert order["fulfillment_status"] == "delivered"
    assert prompts["items"]
    assert review["purchase_evidence"] == "buywise_recorded"
    if ai is not None:
        assert ai["product_count"] > 0
        assert ai["degraded"] is False


def _first_product_id(products: dict[str, Any]) -> int:
    if not products.get("items"):
        raise SystemExit("Product list is empty.")
    return int(products["items"][0]["id"])


def _matching_prompt(prompts: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    order_item_ids = {item["id"] for item in order.get("items", [])}
    for prompt in prompts.get("items", []):
        if prompt.get("order_item_id") in order_item_ids:
            return prompt
    raise SystemExit("Smoke order did not produce a feedback prompt.")


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    data = None
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} failed: HTTP {exc.code} {body}") from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BuyWise closed beta smoke checks.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True, help="Bearer token for the smoke subject.")
    parser.add_argument("--readiness-token", required=True)
    parser.add_argument("--include-ai", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
