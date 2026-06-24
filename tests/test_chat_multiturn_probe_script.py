from scripts import chat_multiturn_probe


def test_chat_multiturn_probe_reports_expected_scenarios(monkeypatch) -> None:
    json_calls = []
    sse_calls = []
    state = {"explicit_added": False}

    def fake_request_json(method, url, payload=None, headers=None):
        json_calls.append({"method": method, "url": url, "payload": payload, "headers": headers or {}})
        if url.endswith("/api/v1/cart"):
            return {"items": [{"product_id": 1}]} if state["explicit_added"] else {"items": []}
        message = (payload or {}).get("message", "")
        if message == "预算改到500":
            return {
                "structured_need": {
                    "category": "机械键盘",
                    "budget_max": 500,
                    "scenario": "宿舍",
                    "preferences": ["低噪音", "无线"],
                    "avoid": [],
                },
                "products": [{"id": 1}],
                "extra": {},
            }
        if message == "不要无线":
            return {
                "structured_need": {
                    "category": "机械键盘",
                    "budget_max": 500,
                    "scenario": "宿舍",
                    "preferences": ["低噪音"],
                    "avoid": ["无线"],
                },
                "products": [{"id": 1}],
                "extra": {},
            }
        if message == "换成办公用":
            return {
                "structured_need": {
                    "category": "机械键盘",
                    "budget_max": 300,
                    "scenario": "办公",
                    "preferences": ["低噪音", "无线"],
                    "avoid": [],
                },
                "products": [{"id": 2}],
                "extra": {},
            }
        if message == "把刚才那款加到购物车":
            state["explicit_added"] = True
            return {"structured_need": None, "products": [], "extra": {"action": "cart.add", "product_ids": [1]}}
        if "加购" in message:
            return {"structured_need": {"category": "机械键盘"}, "products": [{"id": 1}], "extra": {}}
        return {"structured_need": {"category": "机械键盘"}, "products": [{"id": 1}], "extra": {}}

    def fake_request_sse(url, payload):
        sse_calls.append({"url": url, "payload": payload})
        if payload["message"] == "为什么推荐它？":
            return [
                {"event": "meta", "data": {"session_id": payload["session_id"]}},
                {"event": "status", "data": {"stage": "generation", "message": "follow_up_generation"}},
                {"event": "token", "data": {"text": "因为符合预算。"}},
                {"event": "done", "data": {"reply": "因为符合预算。", "should_refresh": False}},
            ]
        if "/guide/stream" in url:
            return [
                {"event": "meta", "data": {"session_id": payload["session_id"]}},
                {"event": "products", "data": {"items": [{"id": 1}]}},
                {"event": "done", "data": {"reply": "推荐完成"}},
            ]
        return [
            {"event": "meta", "data": {"session_id": payload["session_id"]}},
            {"event": "status", "data": {"stage": "refresh", "message": "needs_new_recommendation"}},
            {"event": "done", "data": {"should_refresh": True, "refresh_reason": "needs_new_recommendation"}},
        ]

    monkeypatch.setattr(chat_multiturn_probe, "request_json", fake_request_json)
    monkeypatch.setattr(chat_multiturn_probe, "request_sse", fake_request_sse)

    report = chat_multiturn_probe.run_probe("http://local.test", token="token")

    assert report["status"] == "ok"
    assert {scenario["name"] for scenario in report["scenarios"]} == {
        "json_budget_update",
        "json_scenario_update",
        "json_negative_preference",
        "ambiguous_add_to_cart",
        "explicit_add_to_cart",
        "follow_up_refresh",
        "follow_up_explains_snapshot",
    }
    assert all(scenario["failed_checks"] == [] for scenario in report["scenarios"])
    assert any(call["headers"].get("Authorization") == "Bearer token" for call in json_calls)
    assert any(call["payload"]["message"] == "预算改到500" for call in sse_calls)
