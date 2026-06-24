"""Guide turn routing for chat streams."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.schemas.chat_stream import ChatStreamStatusEventData
from app.services.guide_follow_up_stream_service import GuideFollowUpStreamService


class ChatStreamGuideTurnMixin:
    async def _generate_guide_from_context(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("meta", self._meta_payload(context))
        yield self._event("status", ChatStreamStatusEventData(stage="intent", message="intent"))
        if request.session_id and context["chat_repo"].list_messages(context["session_id"], limit=1):
            async for event in self._guide_turn_events(context, request, db):
                yield event
            return
        if self._can_use_fast_products(request, db):
            async for event in self._stream_guide_fast_first(context, request, db):
                yield event
            return

        need = await self._extract_need(context, request)
        async for event in self._stream_turn_recommendation(context, request, need, db):
            yield event

    async def _generate_follow_up_from_context(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        yield self._event("meta", self._meta_payload(context))
        async for event in self._guide_turn_events(context, request, db):
            yield event

    async def _guide_turn_events(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in GuideFollowUpStreamService(self.chat_service, self._event).generate_events(
            context,
            request,
            allow_recommendation=True,
            recommendation_handler=lambda next_need: self._stream_turn_recommendation(context, request, next_need, db),
        ):
            yield event

    async def _stream_turn_recommendation(
        self,
        context: dict[str, Any],
        request: ChatRequest,
        need: Any,
        db: Session,
    ) -> AsyncIterator[dict[str, Any]]:
        if need.need_clarify:
            context["stream_path"] = "guide_clarify"
            async for event in self._stream_clarify(context, need):
                yield event
            return
        if self.chat_service._is_out_of_scope_need(need):
            async for event in self._stream_out_of_scope(context, need):
                yield event
            return
        self._apply_preferences(context, request, need, db)
        async for event in self._stream_recommendation(context, need, db):
            yield event
