"""Chat API endpoints."""

import asyncio
import inspect
import json
import time
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_chat_service, get_compare_service
from app.core.providers import Principal, get_auth_provider
from app.core.traffic import check_chat_session_rate_limit
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.chat_stream import ChatStreamDoneEventData, ChatStreamErrorEventData
from app.schemas.compare import CompareFollowUpRequest
from app.schemas.guide_session import GuideSessionCreateResponse, GuideSessionDetail, GuideSessionListResponse
from app.services.chat_service import ChatService
from app.services.compare_service import CompareService
from app.services.guide_session_service import GuideSessionService


router = APIRouter(prefix="/ai")


@router.post("/guide/sessions", response_model=GuideSessionCreateResponse)
def create_guide_session(http_request: Request, db: Session = Depends(get_db)) -> GuideSessionCreateResponse:
    return GuideSessionService(db).create(_optional_principal(http_request))


@router.get("/guide/sessions", response_model=GuideSessionListResponse)
def list_guide_sessions(
    http_request: Request,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> GuideSessionListResponse:
    return GuideSessionService(db).list_for_principal(_optional_principal(http_request), max(1, min(limit, 50)))


@router.get("/guide/sessions/{session_id}", response_model=GuideSessionDetail)
def get_guide_session(
    session_id: str,
    http_request: Request,
    session_token: str | None = None,
    db: Session = Depends(get_db),
) -> GuideSessionDetail:
    return GuideSessionService(db).get_detail(session_id, _optional_principal(http_request), session_token)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    request: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    check_chat_session_rate_limit(request.session_id)
    return await _handle_chat(service, request, db, _optional_principal(http_request))


@router.post("/chat/stream")
async def stream_chat(
    http_request: Request,
    request: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    app_settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    check_chat_session_rate_limit(request.session_id)

    async def event_stream():
        events = _generate_chat_stream(service, request, db, _optional_principal(http_request))
        async for event in _stream_with_keepalive(events, request.session_id, app_settings):
            yield _format_sse(event["event"], event["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/guide/stream")
async def stream_guide(
    http_request: Request,
    request: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    app_settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    check_chat_session_rate_limit(request.session_id)

    async def event_stream():
        events = _generate_guide_stream(service, request, db, _optional_principal(http_request))
        async for event in _stream_with_keepalive(events, request.session_id, app_settings):
            yield _format_sse(event["event"], event["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/guide/follow-up/stream")
async def stream_guide_follow_up(
    http_request: Request,
    request: ChatRequest,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    app_settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    check_chat_session_rate_limit(request.session_id)

    async def event_stream():
        events = _generate_follow_up_stream(service, request, db, _optional_principal(http_request))
        async for event in _stream_with_keepalive(events, request.session_id, app_settings):
            yield _format_sse(event["event"], event["data"])

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/compare/follow-up/stream")
async def stream_compare_follow_up(
    request: CompareFollowUpRequest,
    service: CompareService = Depends(get_compare_service),
    app_settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    check_chat_session_rate_limit(request.session_id)

    async def event_stream():
        events = service.generate_follow_up_stream(request)
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
    has_products = False
    try:
        while time.monotonic() < deadline:
            pending = pending or asyncio.create_task(iterator.__anext__())
            event = await _next_stream_event(pending, deadline, app_settings)
            if event is None:
                yield _heartbeat_event()
                continue
            pending = None
            has_products = has_products or _is_product_result_event(event)
            yield event
            if event["event"] in {"done", "error"}:
                return
        yield _partial_done_event() if has_products else _timeout_event(session_id)
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


def _partial_done_event() -> dict[str, Any]:
    return {
        "event": "done",
        "data": ChatStreamDoneEventData(
            reply="导购总结生成较慢，已先返回商品候选。你可以先查看商品卡片，或继续追问具体差异。",
            degraded=True,
            degraded_reason="stream_generation_timeout",
        ),
    }


def _is_product_result_event(event: dict[str, Any]) -> bool:
    if event.get("event") != "products":
        return False
    data = event.get("data") or {}
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    return bool(data.get("items") or data.get("bundle_plans"))


def _heartbeat_seconds(app_settings: Settings) -> float:
    return max(0.01, app_settings.chat_stream_heartbeat_seconds)


def _stream_max_seconds(app_settings: Settings) -> float:
    return max(_heartbeat_seconds(app_settings), app_settings.chat_stream_max_seconds)


def _format_sse(event: str, data: dict) -> str:
    payload = json.dumps(jsonable_encoder(data), ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def _generate_chat_stream(service: ChatService, request: ChatRequest, db: Session, principal: Principal | None):
    parameters = inspect.signature(service.generate_chat_stream).parameters
    if "principal" in parameters:
        return service.generate_chat_stream(request, db, principal=principal)
    if "user_id" in parameters:
        return service.generate_chat_stream(request, db, user_id=_principal_user_id(principal))
    return service.generate_chat_stream(request, db)


def _generate_guide_stream(service: ChatService, request: ChatRequest, db: Session, principal: Principal | None):
    parameters = inspect.signature(service.generate_guide_stream).parameters
    if "principal" in parameters:
        return service.generate_guide_stream(request, db, principal=principal)
    if "user_id" in parameters:
        return service.generate_guide_stream(request, db, user_id=_principal_user_id(principal))
    return service.generate_guide_stream(request, db)


def _generate_follow_up_stream(service: ChatService, request: ChatRequest, db: Session, principal: Principal | None):
    parameters = inspect.signature(service.generate_follow_up_stream).parameters
    if "principal" in parameters:
        return service.generate_follow_up_stream(request, db, principal=principal)
    if "user_id" in parameters:
        return service.generate_follow_up_stream(request, db, user_id=_principal_user_id(principal))
    return service.generate_follow_up_stream(request, db)


async def _handle_chat(service: ChatService, request: ChatRequest, db: Session, principal: Principal | None) -> ChatResponse:
    parameters = inspect.signature(service.handle_chat).parameters
    if "principal" in parameters:
        return await service.handle_chat(request, db, principal=principal)
    if "user_id" in parameters:
        return await service.handle_chat(request, db, user_id=_principal_user_id(principal))
    return await service.handle_chat(request, db)


def _optional_principal(request: Request) -> Principal | None:
    return get_auth_provider().get_current_principal(request)


def _principal_user_id(principal: Principal | None) -> int | None:
    if principal is None or principal.auth_type != "user" or not principal.subject.startswith("user:"):
        return None
    try:
        return int(principal.subject.split(":", 1)[1])
    except ValueError:
        return None
