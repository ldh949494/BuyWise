"""Chat session ownership and anonymous token handling."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.core.metrics import count_chat_session_forbidden
from app.core.providers import AppError, Principal


@dataclass(frozen=True)
class ChatSessionContext:
    session_id: str
    session_token: str | None
    owner_subject: str | None
    owner_auth_type: str | None
    user_id: int | None


class ChatSessionSecurityService:
    def get_or_create_context(
        self,
        chat_repo: Any,
        *,
        session_id: str | None,
        title: str | None,
        principal: Principal | None,
        session_token: str | None,
    ) -> ChatSessionContext:
        session = chat_repo.get_session(session_id) if session_id else None
        if session is None:
            return self._create_context(chat_repo, session_id, title, principal)
        self._authorize_existing(session, principal, session_token)
        self._claim_if_authenticated(session, principal, session_token)
        chat_repo.update_session_activity(session, self._expires_at(principal))
        return self._context(session, None, principal)

    def _create_context(
        self,
        chat_repo: Any,
        session_id: str | None,
        title: str | None,
        principal: Principal | None,
    ) -> ChatSessionContext:
        token = self._new_token() if self._should_issue_token(principal) else None
        session = chat_repo.create_session(
            session_id=session_id,
            title=title,
            owner_subject=self._owner_subject(principal),
            owner_auth_type=self._owner_auth_type(principal),
            user_id=self._principal_user_id(principal),
            session_token_hash=self._hash_token(token),
            expires_at=self._expires_at(principal),
        )
        return self._context(session, token, principal)

    def _authorize_existing(self, session: Any, principal: Principal | None, session_token: str | None) -> None:
        if not settings.chat_session_tokens_enabled:
            return
        if self._is_owner(session, principal):
            return
        if self._valid_session_token(session, session_token):
            return
        count_chat_session_forbidden("owner_mismatch")
        raise AppError("Chat session is not accessible.", status_code=403, code="chat_session_forbidden")

    def _claim_if_authenticated(self, session: Any, principal: Principal | None, session_token: str | None) -> None:
        if principal is None or not self._valid_session_token(session, session_token):
            return
        session.owner_subject = self._owner_subject(principal)
        session.owner_auth_type = self._owner_auth_type(principal)
        session.user_id = self._principal_user_id(principal)
        session.session_token_hash = None

    def _context(self, session: Any, token: str | None, principal: Principal | None) -> ChatSessionContext:
        return ChatSessionContext(
            session_id=session.session_id,
            session_token=token,
            owner_subject=getattr(session, "owner_subject", None) or self._owner_subject(principal),
            owner_auth_type=getattr(session, "owner_auth_type", None) or self._owner_auth_type(principal),
            user_id=getattr(session, "user_id", None) or self._principal_user_id(principal),
        )

    def _is_owner(self, session: Any, principal: Principal | None) -> bool:
        owner = getattr(session, "owner_subject", None)
        return bool(owner and owner == self._owner_subject(principal))

    def _valid_session_token(self, session: Any, token: str | None) -> bool:
        expected = getattr(session, "session_token_hash", None)
        if not expected or not token:
            return False
        if self._is_expired(session):
            count_chat_session_forbidden("expired")
            return False
        return secrets.compare_digest(expected, self._hash_token(token) or "")

    def _is_expired(self, session: Any) -> bool:
        expires_at = getattr(session, "expires_at", None)
        return bool(expires_at and expires_at < datetime.utcnow())

    def _should_issue_token(self, principal: Principal | None) -> bool:
        return settings.chat_session_tokens_enabled and principal is None

    def _expires_at(self, principal: Principal | None) -> datetime | None:
        if principal is not None:
            return None
        return datetime.utcnow() + timedelta(hours=max(settings.chat_anon_session_ttl_hours, 1))

    def _owner_subject(self, principal: Principal | None) -> str | None:
        return principal.subject if principal is not None else None

    def _owner_auth_type(self, principal: Principal | None) -> str | None:
        return principal.auth_type if principal is not None else "anonymous"

    def _principal_user_id(self, principal: Principal | None) -> int | None:
        if principal is None or principal.auth_type != "user" or not principal.subject.startswith("user:"):
            return None
        try:
            return int(principal.subject.split(":", 1)[1])
        except ValueError:
            return None

    def _new_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _hash_token(self, token: str | None) -> str | None:
        if token is None:
            return None
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
