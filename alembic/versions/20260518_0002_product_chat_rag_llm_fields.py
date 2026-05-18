"""Add product and recommendation explanation fields.

Revision ID: 20260518_0002
Revises: 20260515_0001
Create Date: 2026-05-18 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260518_0002"
down_revision = "20260515_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("sku", sa.String(length=128), nullable=True))
    op.add_column("products", sa.Column("product_url", sa.String(length=1024), nullable=True))
    op.add_column("products", sa.Column("image_urls", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("stock_status", sa.String(length=32), nullable=True))
    op.add_column("products", sa.Column("review_summary", sa.Text(), nullable=True))
    op.add_column("recommendations", sa.Column("explanation", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("recommendations", "explanation")
    op.drop_column("products", "review_summary")
    op.drop_column("products", "stock_status")
    op.drop_column("products", "image_urls")
    op.drop_column("products", "product_url")
    op.drop_column("products", "sku")
