"""Agent action audit repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_action import AgentAction


class AgentActionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_action(self, action: AgentAction) -> AgentAction:
        self.db.add(action)
        self.db.flush()
        return action

    def get_pending_action(self, action_id: str, owner_subject: str | None) -> AgentAction | None:
        statement = select(AgentAction).where(
            AgentAction.action_id == action_id,
            AgentAction.status == "pending_confirmation",
            AgentAction.owner_subject == owner_subject,
        )
        return self.db.scalar(statement)
