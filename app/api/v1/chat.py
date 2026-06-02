"""Chat API endpoints."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.chat_stream import ChatStreamErrorEventData
from app.services.chat_service import ChatService


router = APIRouter(prefix="/ai")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.handle_chat(request, db)


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    app_settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    async def event_stream():
        events = service.generate_chat_stream(request, db)
        async for event in _stream_with_keepalive(events, request.session_id, app_settings):
            yield _format_sse(event["event"], event["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _stream_with_keepalive(
    events: AsyncIterator[dict[str, Any]],
    session_id: str | None,
    app_settings: Settings,
) -> AsyncIterator[dict[str, Any]]:
    deadline = time.monotonic() + _stream_max_seconds(app_settings)
    iterator = events.__aiter__()
    pending: asyncio.Task | None = None
    try:
        while time.monotonic() < deadline:
            pending = pending or asyncio.create_task(iterator.__anext__())
            event = await _next_stream_event(pending, deadline, app_settings)
            if event is None:
                yield _heartbeat_event()
                continue
            pending = None
            yield event
            if event["event"] in {"done", "error"}:
                return
        yield _timeout_event(session_id)
    except StopAsyncIteration:
        return
    finally:
        await _close_stream_iterator(iterator, pending)


async def _next_stream_event(
    pending: asyncio.Task,
    deadline: float,
    app_settings: Settings,
) -> dict[str, Any] | None:
    timeout = min(_heartbeat_seconds(app_settings), max(0.0, deadline - time.monotonic()))
    try:
        return await asyncio.wait_for(asyncio.shield(pending), timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def _close_stream_iterator(iterator: AsyncIterator[dict[str, Any]], pending: asyncio.Task | None) -> None:
    if pending is not None and not pending.done():
        pending.cancel()
        with suppress(asyncio.CancelledError):
            await pending
    close = getattr(iterator, "aclose", None)
    if callable(close):
        await close()


def _heartbeat_event() -> dict[str, Any]:
    return {"event": "heartbeat", "data": {"status": "ok"}}


def _timeout_event(session_id: str | None) -> dict[str, Any]:
    return {
        "event": "error",
        "data": ChatStreamErrorEventData(
            code="chat_stream_timeout",
            message="chat_stream_timeout",
            session_id=session_id or "unknown",
        ),
    }


def _heartbeat_seconds(app_settings: Settings) -> float:
    return max(0.01, app_settings.chat_stream_heartbeat_seconds)


def _stream_max_seconds(app_settings: Settings) -> float:
    return max(_heartbeat_seconds(app_settings), app_settings.chat_stream_max_seconds)


def _format_sse(event: str, data: dict) -> str:
    payload = json.dumps(jsonable_encoder(data), ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"
