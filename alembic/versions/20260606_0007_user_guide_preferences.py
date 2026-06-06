"""Add user guide preferences."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260606_0007"
down_revision = "20260601_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_guide_preferences",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("budget_policy", sa.String(length=32), nullable=False),
        sa.Column("presentation_style", sa.String(length=32), nullable=False),
        sa.Column("preferences_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_guide_preferences_user_id", "user_guide_preferences", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_guide_preferences_user_id", table_name="user_guide_preferences")
    op.drop_table("user_guide_preferences")
