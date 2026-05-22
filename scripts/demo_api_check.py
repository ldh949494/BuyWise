from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


DEMO_QUESTION = "帮我推荐一个300以内适合宿舍写代码的低噪音无线机械键盘，最好性价比高"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the BuyWise demo API fallback checks.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    result = run_checks(base_url)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def run_checks(base_url: str) -> dict[str, Any]:
    health = request_json("GET", f"{base_url}/api/v1/health")
    products = request_json("GET", f"{base_url}/api/v1/products?page=1&page_size=5")
    compare = request_json(
        "POST",
        f"{base_url}/api/v1/products/compare",
        {"product_ids": [1101, 1001], "user_need": "宿舍写代码，预算300以内，安静无线"},
    )
    chat = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": "demo-api-check", "message": DEMO_QUESTION},
    )

    assert health["status"] == "ok"
    assert products["items"]
    assert compare["items"]
    assert chat["products"]
    assert chat["products"][0]["id"] == 1101

    return {
        "health": health,
        "first_product": products["items"][0]["name"],
        "compare_winner_id": compare["winner_id"],
        "chat_top_product": chat["products"][0]["name"],
    }


def request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} failed: HTTP {exc.code} {body}") from exc


if __name__ == "__main__":
    main()
