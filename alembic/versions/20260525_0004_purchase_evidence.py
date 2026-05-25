"""Add purchase evidence to reviews.

Revision ID: 20260525_0004
Revises: 20260523_0003
Create Date: 2026-05-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_0004"
down_revision = "20260523_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("purchase_evidence", sa.String(length=32), nullable=True))
    op.create_index("ix_reviews_purchase_evidence", "reviews", ["purchase_evidence"])


def downgrade() -> None:
    op.drop_index("ix_reviews_purchase_evidence", table_name="reviews")
    op.drop_column("reviews", "purchase_evidence")
