"""Initial schema.

Revision ID: 20260515_0001
Revises:
Create Date: 2026-05-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260515_0001"
down_revision = None
branch_labels = None
depends_on = None


def id_column() -> sa.Column:
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        id_column(),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("structured_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    op.create_table(
        "chat_sessions",
        id_column(),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_chat_sessions_session_id", "chat_sessions", ["session_id"])

    op.create_table(
        "price_history",
        id_column(),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
    )
    op.create_index("ix_price_history_date", "price_history", ["date"])
    op.create_index("ix_price_history_product_id", "price_history", ["product_id"])

    op.create_table(
        "products",
        id_column(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("brand", sa.String(length=64), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("original_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("sales", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specs", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("suitable_scene", sa.JSON(), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_price", "products", ["price"])

    op.create_table(
        "recommendations",
        id_column(),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_recommendations_product_id", "recommendations", ["product_id"])
    op.create_index("ix_recommendations_session_id", "recommendations", ["session_id"])

    op.create_table(
        "reviews",
        id_column(),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("user_name", sa.String(length=64), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_product_id", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_recommendations_session_id", table_name="recommendations")
    op.drop_index("ix_recommendations_product_id", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index("ix_products_price", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_price_history_product_id", table_name="price_history")
    op.drop_index("ix_price_history_date", table_name="price_history")
    op.drop_table("price_history")
    op.drop_index("ix_chat_sessions_session_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")
