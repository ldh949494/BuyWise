import sys

from scripts import demo_api_check


def test_demo_api_check_main_requests_expected_fallback_flow(monkeypatch, capsys) -> None:
    calls = []

    def fake_request_json(method, url, payload=None):
        calls.append({"method": method, "url": url, "payload": payload})
        if url.endswith("/api/v1/health"):
            return {"status": "ok", "service": "BuyWise Backend"}
        if url.endswith("/api/v1/products?page=1&page_size=5"):
            return {"items": [{"name": "Campus75 三模静音机械键盘"}]}
        if url.endswith("/api/v1/products/compare"):
            return {"winner_id": 1101, "items": [{"id": 1101}]}
        if url.endswith("/api/v1/ai/chat"):
            return {"products": [{"id": 1101, "name": "Campus75 三模静音机械键盘"}]}
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(demo_api_check, "request_json", fake_request_json)
    monkeypatch.setattr(sys, "argv", ["demo_api_check.py", "--base-url", "http://demo.local/"])

    demo_api_check.main()

    assert [call["method"] for call in calls] == ["GET", "GET", "POST", "POST"]
    assert calls[2]["payload"]["product_ids"] == [1101, 1001]
    assert "低噪音无线机械键盘" in calls[3]["payload"]["message"]
    output = capsys.readouterr().out
    assert "Campus75 三模静音机械键盘" in output
