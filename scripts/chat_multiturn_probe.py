from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any
import urllib.error
import urllib.request


def main() -> None:
    args = _parse_args()
    report = run_probe(args.base_url.rstrip("/"), token=args.token)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "ok":
        raise SystemExit(1)


def run_probe(base_url: str, token: str = "") -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("chat-probe-%Y%m%d-%H%M%S")
    headers = _auth_headers(token)
    scenarios = [
        _probe_json_budget_update(base_url, run_id),
        _probe_json_scenario_update(base_url, run_id),
        _probe_json_negative_preference(base_url, run_id),
        _probe_ambiguous_add_to_cart(base_url, run_id, headers),
        _probe_explicit_add_to_cart(base_url, run_id, headers),
        _probe_follow_up_refresh(base_url, run_id),
        _probe_follow_up_explains_snapshot(base_url, run_id),
    ]
    return {
        "run_id": run_id,
        "status": "ok" if all(item["passed"] for item in scenarios) else "failed",
        "scenarios": scenarios,
    }


def _probe_json_budget_update(base_url: str, run_id: str) -> dict[str, Any]:
    session_id = f"{run_id}-budget"
    request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    response = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "预算改到500"},
    )
    need = response.get("structured_need") or {}
    checks = {
        "category": need.get("category") == "机械键盘",
        "budget_max": need.get("budget_max") == 500,
        "scenario": need.get("scenario") == "宿舍",
        "products": bool(response.get("products")),
    }
    return _scenario("json_budget_update", checks, {"need": need, "product_count": len(response.get("products") or [])})


def _probe_json_negative_preference(base_url: str, run_id: str) -> dict[str, Any]:
    session_id = f"{run_id}-negative"
    request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "推荐一个500以内适合宿舍的低噪音无线机械键盘"},
    )
    response = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "不要无线"},
    )
    need = response.get("structured_need") or {}
    preferences = need.get("preferences") or []
    avoid = need.get("avoid") or []
    checks = {
        "category": need.get("category") == "机械键盘",
        "avoid_wireless": "无线" in avoid,
        "wireless_removed": "无线" not in preferences,
    }
    return _scenario("json_negative_preference", checks, {"need": need})


def _probe_json_scenario_update(base_url: str, run_id: str) -> dict[str, Any]:
    session_id = f"{run_id}-scenario"
    request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    response = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "换成办公用"},
    )
    need = response.get("structured_need") or {}
    checks = {
        "category": need.get("category") == "机械键盘",
        "budget_max": need.get("budget_max") == 300,
        "scenario": need.get("scenario") == "办公",
        "products": bool(response.get("products")),
    }
    return _scenario(
        "json_scenario_update",
        checks,
        {"need": need, "product_count": len(response.get("products") or [])},
    )


def _probe_ambiguous_add_to_cart(base_url: str, run_id: str, headers: dict[str, str]) -> dict[str, Any]:
    session_id = f"{run_id}-ambiguous-add"
    request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    response = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "帮我加购一副合适的键盘到购物车"},
    )
    cart = request_json("GET", f"{base_url}/api/v1/cart", headers=headers) if headers else {"items": []}
    action = (response.get("extra") or {}).get("action")
    checks = {
        "no_cart_add_action": action != "cart.add",
        "cart_unchanged_when_readable": not (cart.get("items") or []),
    }
    return _scenario("ambiguous_add_to_cart", checks, {"action": action, "cart_items": cart.get("items", [])})


def _probe_explicit_add_to_cart(base_url: str, run_id: str, headers: dict[str, str]) -> dict[str, Any]:
    session_id = f"{run_id}-explicit-add"
    request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    response = request_json(
        "POST",
        f"{base_url}/api/v1/ai/chat",
        {"session_id": session_id, "message": "把刚才那款加到购物车"},
        headers=headers or None,
    )
    action = (response.get("extra") or {}).get("action")
    cart = request_json("GET", f"{base_url}/api/v1/cart", headers=headers) if headers else {}
    cart_items = cart.get("items", []) if headers else []
    checks = {
        "cart_add_action": action == "cart.add" if headers else action in {"cart.add", "cart.add.needs_context"},
        "cart_written_when_readable": bool(cart_items) if headers and action == "cart.add" else True,
    }
    return _scenario(
        "explicit_add_to_cart",
        checks,
        {"action": action, "product_ids": (response.get("extra") or {}).get("product_ids"), "cart_items": cart_items},
    )


def _probe_follow_up_refresh(base_url: str, run_id: str) -> dict[str, Any]:
    session_id = f"{run_id}-follow-up-refresh"
    request_sse(
        f"{base_url}/api/v1/ai/guide/stream",
        {"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    events = request_sse(
        f"{base_url}/api/v1/ai/guide/follow-up/stream",
        {"session_id": session_id, "message": "预算改到500"},
    )
    done = next((event for event in reversed(events) if event.get("event") == "done"), {})
    data = done.get("data") or {}
    checks = {
        "done": bool(done),
        "should_refresh": data.get("should_refresh") is True,
        "refresh_reason": data.get("refresh_reason") == "needs_new_recommendation",
        "event_order": _events_in_order(events, ["meta", "status", "done"]),
    }
    return _scenario("follow_up_refresh", checks, {"events": _event_names(events), "done": data})


def _probe_follow_up_explains_snapshot(base_url: str, run_id: str) -> dict[str, Any]:
    session_id = f"{run_id}-follow-up-explain"
    start_events = request_sse(
        f"{base_url}/api/v1/ai/guide/stream",
        {"session_id": session_id, "message": "推荐一个300以内适合宿舍的低噪音无线机械键盘"},
    )
    events = request_sse(
        f"{base_url}/api/v1/ai/guide/follow-up/stream",
        {"session_id": session_id, "message": "为什么推荐它？"},
    )
    done = next((event for event in reversed(events) if event.get("event") == "done"), {})
    data = done.get("data") or {}
    checks = {
        "start_has_products": any(event.get("event") == "products" for event in start_events),
        "done": bool(done),
        "no_refresh": data.get("should_refresh") is False,
        "has_reply": bool(data.get("reply")),
        "event_order": _events_in_order(events, ["meta", "status", "done"]),
    }
    return _scenario("follow_up_explains_snapshot", checks, {"events": _event_names(events), "done": data})


def _event_names(events: list[dict[str, Any]]) -> list[str]:
    return [str(event.get("event")) for event in events]


def _events_in_order(events: list[dict[str, Any]], expected: list[str]) -> bool:
    names = _event_names(events)
    cursor = 0
    for name in expected:
        try:
            cursor = names.index(name, cursor) + 1
        except ValueError:
            return False
    return True


def _failed_checks(checks: dict[str, bool]) -> list[str]:
    return [name for name, passed in checks.items() if not passed]


def _scenario(name: str, checks: dict[str, bool], actual: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "passed": all(checks.values()),
        "checks": checks,
        "failed_checks": _failed_checks(checks),
        "actual": actual,
    }


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
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} failed: HTTP {exc.code} {body}") from exc


def request_sse(url: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    text = _request_text("POST", url, payload)
    events = []
    for block in text.strip().split("\n\n"):
        event_name = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line.removeprefix("event: ").strip()
            elif line.startswith("data: "):
                data = json.loads(line.removeprefix("data: ").strip())
        if event_name is not None:
            events.append({"event": event_name, "data": data or {}})
    return events


def _request_text(method: str, url: str, payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Accept": "text/event-stream", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} failed: HTTP {exc.code} {body}") from exc


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe BuyWise multi-turn chat accuracy over HTTP.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", default="", help="Optional Bearer token for prod cart checks.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
