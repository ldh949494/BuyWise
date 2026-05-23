"""Add simulated order feedback loop.

Revision ID: 20260523_0003
Revises: 20260518_0002
Create Date: 2026-05-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260523_0003"
down_revision = "20260518_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("user_ref", sa.String(length=128), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("fulfillment_status", sa.String(length=32), nullable=False),
        sa.Column("external_platform", sa.String(length=64), nullable=True),
        sa.Column("external_order_ref", sa.String(length=128), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("shipped_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_orders_user_ref", "orders", ["user_ref"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("platform_snapshot", sa.String(length=64), nullable=True),
        sa.Column("product_url_snapshot", sa.String(length=1024), nullable=True),
        sa.Column("feedback_due_at", sa.DateTime(), nullable=True),
        sa.Column("feedback_submitted_at", sa.DateTime(), nullable=True),
        sa.Column("feedback_prompt_dismissed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_index("ix_order_items_feedback_due_at", "order_items", ["feedback_due_at"])

    op.add_column("reviews", sa.Column("order_item_id", sa.BigInteger(), nullable=True))
    op.add_column("reviews", sa.Column("user_ref", sa.String(length=128), nullable=True))
    op.add_column("reviews", sa.Column("source", sa.String(length=32), nullable=True))
    op.add_column("reviews", sa.Column("verified_purchase", sa.Boolean(), nullable=True))
    op.add_column("reviews", sa.Column("usage_context", sa.String(length=64), nullable=True))
    op.add_column("reviews", sa.Column("pros_tags", sa.JSON(), nullable=True))
    op.add_column("reviews", sa.Column("cons_tags", sa.JSON(), nullable=True))
    op.add_column("reviews", sa.Column("met_expectation", sa.Boolean(), nullable=True))
    op.add_column("reviews", sa.Column("status", sa.String(length=32), nullable=True))
    op.add_column("reviews", sa.Column("submitted_at", sa.DateTime(), nullable=True))
    op.add_column("reviews", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_reviews_order_item_id", "reviews", ["order_item_id"])
    op.create_index("ix_reviews_source", "reviews", ["source"])
    op.create_index("ix_reviews_user_ref", "reviews", ["user_ref"])


def downgrade() -> None:
    op.drop_index("ix_reviews_user_ref", table_name="reviews")
    op.drop_index("ix_reviews_source", table_name="reviews")
    op.drop_index("ix_reviews_order_item_id", table_name="reviews")
    op.drop_column("reviews", "updated_at")
    op.drop_column("reviews", "submitted_at")
    op.drop_column("reviews", "status")
    op.drop_column("reviews", "met_expectation")
    op.drop_column("reviews", "cons_tags")
    op.drop_column("reviews", "pros_tags")
    op.drop_column("reviews", "usage_context")
    op.drop_column("reviews", "verified_purchase")
    op.drop_column("reviews", "source")
    op.drop_column("reviews", "user_ref")
    op.drop_column("reviews", "order_item_id")

    op.drop_index("ix_order_items_feedback_due_at", table_name="order_items")
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_user_ref", table_name="orders")
    op.drop_table("orders")
