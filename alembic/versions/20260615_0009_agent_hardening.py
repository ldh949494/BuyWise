"""Add agent session ownership and action audit."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260615_0009"
down_revision = "20260609_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _add_chat_session_columns()
    _create_agent_actions()


def downgrade() -> None:
    _drop_agent_actions()
    _drop_chat_session_columns()


def _add_chat_session_columns() -> None:
    op.add_column("chat_sessions", sa.Column("owner_subject", sa.String(length=128), nullable=True))
    op.add_column("chat_sessions", sa.Column("owner_auth_type", sa.String(length=32), nullable=True))
    op.add_column("chat_sessions", sa.Column("session_token_hash", sa.String(length=128), nullable=True))
    op.add_column("chat_sessions", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("chat_sessions", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("chat_sessions", sa.Column("context_summary", sa.Text(), nullable=True))
    op.create_index("ix_chat_sessions_owner_subject", "chat_sessions", ["owner_subject"])
    op.create_index("ix_chat_sessions_expires_at", "chat_sessions", ["expires_at"])


def _drop_chat_session_columns() -> None:
    op.drop_index("ix_chat_sessions_expires_at", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_owner_subject", table_name="chat_sessions")
    op.drop_column("chat_sessions", "context_summary")
    op.drop_column("chat_sessions", "updated_at")
    op.drop_column("chat_sessions", "expires_at")
    op.drop_column("chat_sessions", "session_token_hash")
    op.drop_column("chat_sessions", "owner_auth_type")
    op.drop_column("chat_sessions", "owner_subject")


def _create_agent_actions() -> None:
    op.create_table(
        "agent_actions",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("owner_subject", sa.String(length=128), nullable=True),
        sa.Column("owner_auth_type", sa.String(length=32), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("confirmation_required", sa.Boolean(), nullable=False),
        sa.Column("resolved_payload", sa.JSON(), nullable=True),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_agent_actions_action_id", "agent_actions", ["action_id"], unique=True)
    op.create_index("ix_agent_actions_session_id", "agent_actions", ["session_id"])
    op.create_index("ix_agent_actions_owner_subject", "agent_actions", ["owner_subject"])
    op.create_index("ix_agent_actions_status", "agent_actions", ["status"])


def _drop_agent_actions() -> None:
    op.drop_index("ix_agent_actions_status", table_name="agent_actions")
    op.drop_index("ix_agent_actions_owner_subject", table_name="agent_actions")
    op.drop_index("ix_agent_actions_session_id", table_name="agent_actions")
    op.drop_index("ix_agent_actions_action_id", table_name="agent_actions")
    op.drop_table("agent_actions")
