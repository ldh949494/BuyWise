"""No-op chat repository for service tests and non-SQL sessions."""

from __future__ import annotations

from typing import Any


class NoopChatRepository:
    def __init__(self, session_id: str | None) -> None:
        self.session_id = session_id or "mock-session"

    def get_or_create_session(self, session_id: str | None = None, title: str | None = None) -> Any:
        return type("ChatSessionStub", (), {"session_id": session_id or self.session_id})()

    def create_message(self, *args: Any, **kwargs: Any) -> None:
        return None

    def create_recommendations(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    def list_messages(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    def update_commit(self) -> None:
        return None

    def update_rollback(self) -> None:
        return None

    def generate_session_id(self) -> str:
        return self.session_id
