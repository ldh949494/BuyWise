from fastapi.testclient import TestClient

from app.core.dependencies import get_chat_service
from app.main import create_app


class FakeStreamChatService:
    async def generate_chat_stream(self, request, db):
        yield {"event": "meta", "data": {"session_id": request.session_id or "generated"}}
        yield {"event": "status", "data": {"stage": "intent", "message": "intent"}}
        yield {"event": "token", "data": {"text": "hello"}}
        yield {
            "event": "products",
            "data": {
                "need_clarify": False,
                "structured_need": {"intent": "商品推荐", "category": "机械键盘"},
                "items": [{"id": 1001, "name": "K87", "price": 269.0}],
            },
        }
        yield {"event": "done", "data": {"reply": "hello"}}


def test_chat_stream_endpoint_returns_sse_events() -> None:
    app = create_app()
    app.dependency_overrides[get_chat_service] = lambda: FakeStreamChatService()
    client = TestClient(app)

    with client.stream(
        "POST",
        "/api/v1/ai/chat/stream",
        json={"session_id": "sse-session", "message": "推荐一个键盘"},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert "event: meta" in body
    assert 'data: {"session_id":"sse-session"}' in body
    assert "event: token" in body
    assert 'data: {"text":"hello"}' in body
    assert "event: products" in body
    assert "event: done" in body
