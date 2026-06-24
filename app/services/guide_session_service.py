"""Guide chat session listing and restore service."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.providers import Principal
from app.repositories.chat_repo import ChatRepository
from app.schemas.guide_session import (
    GuideSessionCreateResponse,
    GuideSessionDetail,
    GuideSessionListResponse,
    GuideSessionMessage,
    GuideSessionSummary,
)
from app.services.chat_session_security import ChatSessionSecurityService


class GuideSessionService:
    def __init__(self, db: Session) -> None:
        self.chat_repo = ChatRepository(db)
        self.security = ChatSessionSecurityService()

    def create(self, principal: Principal | None) -> GuideSessionCreateResponse:
        context = self.security.get_or_create_context(
            self.chat_repo,
            session_id=None,
            title="新导购对话",
            principal=principal,
            session_token=None,
        )
        return GuideSessionCreateResponse(session_id=context.session_id, session_token=context.session_token)

    def list_for_principal(self, principal: Principal | None, limit: int) -> GuideSessionListResponse:
        sessions = self.chat_repo.list_sessions(
            owner_subject=principal.subject if principal is not None else None,
            owner_auth_type=principal.auth_type if principal is not None else "anonymous",
            limit=limit,
        )
        return GuideSessionListResponse(items=[self._summary(session) for session in sessions])

    def get_detail(self, session_id: str, principal: Principal | None, session_token: str | None) -> GuideSessionDetail:
        session = self.chat_repo.get_session(session_id)
        if session is None:
            return GuideSessionDetail(session_id=session_id, messages=[])
        self.security._authorize_existing(session, principal, session_token)
        messages = [
            self._message(message)
            for message in self.chat_repo.list_messages(session_id, limit=80)
        ]
        return GuideSessionDetail(session_id=session_id, title=session.title, messages=messages)

    def _summary(self, session: Any) -> GuideSessionSummary:
        messages = self.chat_repo.list_messages(session.session_id, limit=1)
        last_message = messages[-1].content if messages else None
        return GuideSessionSummary(
            session_id=session.session_id,
            title=session.title,
            updated_at=session.updated_at,
            created_at=session.created_at,
            last_message=last_message,
        )

    def _message(self, message: Any) -> GuideSessionMessage:
        structured_data = getattr(message, "structured_data", None) or {}
        return GuideSessionMessage(
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            products=structured_data.get("products") or [],
            bundle_plans=structured_data.get("bundle_plans") or [],
            applied_preferences=structured_data.get("applied_preferences") or {},
            turn_type=structured_data.get("turn_type"),
        )
