import asyncio

from fastapi.testclient import TestClient

from app.api.v1.chat import _format_sse, _stream_with_keepalive
from app.core.config import Settings
from app.core.dependencies import get_chat_service
from app.main import create_app
from app.schemas.chat import BundlePlan, BundlePlanItem, ProductCard, StructuredNeed


class FakeStreamChatService:
    async def generate_chat_stream(self, request, db):
        yield {"event": "meta", "data": {"session_id": request.session_id or "generated"}}
        yield {"event": "status", "data": {"stage": "intent", "message": "intent"}}
        yield {"event": "token", "data": {"text": "hello"}}
        yield {
            "event": "products",
            "data": {
                "need_clarify": False,
                "structured_need": StructuredNeed(intent="商品推荐", category="机械键盘"),
                "items": [ProductCard(id=1001, name="K87", price=269.0)],
            },
        }
        yield {"event": "done", "data": {"reply": "hello", "degraded": False, "degraded_reason": None}}


class FakeBundleStreamChatService:
    async def generate_chat_stream(self, request, db):
        yield {
            "event": "products",
            "data": {
                "need_clarify": False,
                "structured_need": StructuredNeed(intent="bundle_recommend", scenario="桌面"),
                "items": [ProductCard(id=1201, name="DeskMini", price=2599.0)],
                "bundle_plans": [
                    BundlePlan(
                        id="desktop-balanced-6000",
                        title="方案二 · 均衡桌面档",
                        budget_tier="balanced",
                        target_budget=6000,
                        total_price=5899,
                        budget_status="within_budget",
                        items=[
                            BundlePlanItem(
                                category="电脑",
                                product=ProductCard(id=1201, name="DeskMini", price=2599.0),
                                role="性能核心",
                            )
                        ],
                    )
                ],
            },
        }


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
    assert "degraded_reason" in body


def test_chat_stream_endpoint_can_emit_bundle_plans() -> None:
    app = create_app()
    app.dependency_overrides[get_chat_service] = lambda: FakeBundleStreamChatService()
    client = TestClient(app)

    with client.stream(
        "POST",
        "/api/v1/ai/chat/stream",
        json={"session_id": "bundle-session", "message": "配一套桌面装备"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "bundle_plans" in body
    assert "desktop-balanced-6000" in body


def test_format_sse_supports_heartbeat_event() -> None:
    body = _format_sse("heartbeat", {"status": "ok"})

    assert body == 'event: heartbeat\ndata: {"status":"ok"}\n\n'


def test_stream_keepalive_emits_heartbeat_during_idle_gap() -> None:
    async def run() -> list[dict]:
        return await _collect_events(_delayed_done_stream(), _fast_stream_settings())

    events = asyncio.run(run())

    assert {"event": "heartbeat", "data": {"status": "ok"}} in events
    assert events[-1] == {"event": "done", "data": {"reply": "ok"}}


def test_stream_keepalive_times_out_stalled_stream() -> None:
    events = asyncio.run(_collect_events(_stalled_stream(), _fast_stream_settings(max_seconds=0.025)))

    assert events[-1]["event"] == "error"
    assert events[-1]["data"].code == "chat_stream_timeout"
    assert events[-1]["data"].session_id == "sse-session"


async def _delayed_done_stream():
    await asyncio.sleep(0.02)
    yield {"event": "done", "data": {"reply": "ok"}}


async def _stalled_stream():
    await asyncio.sleep(1)
    yield {"event": "done", "data": {"reply": "late"}}


async def _collect_events(stream, settings: Settings) -> list[dict]:
    return [event async for event in _stream_with_keepalive(stream, "sse-session", settings)]


def _fast_stream_settings(max_seconds: float = 1.0) -> Settings:
    return Settings(chat_stream_heartbeat_seconds=0.01, chat_stream_max_seconds=max_seconds)
