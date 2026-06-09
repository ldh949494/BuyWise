"""Add cart, address, checkout, and order snapshots."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260609_0008"
down_revision = "20260606_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "carts",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("user_ref", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_carts_user_ref", "carts", ["user_ref"], unique=True)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("cart_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("image_url_snapshot", sa.String(length=512), nullable=True),
        sa.Column("platform_snapshot", sa.String(length=64), nullable=True),
        sa.Column("product_url_snapshot", sa.String(length=1024), nullable=True),
        sa.Column("source_session_id", sa.String(length=64), nullable=True),
        sa.Column("source_label", sa.String(length=128), nullable=True),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])
    op.create_index("ix_cart_items_product_id", "cart_items", ["product_id"])

    op.create_table(
        "addresses",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("user_ref", sa.String(length=128), nullable=False),
        sa.Column("receiver_name", sa.String(length=64), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("province", sa.String(length=64), nullable=True),
        sa.Column("city", sa.String(length=64), nullable=True),
        sa.Column("district", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_addresses_user_ref", "addresses", ["user_ref"])

    op.create_table(
        "checkout_sessions",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("user_ref", sa.String(length=128), nullable=False),
        sa.Column("cart_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("address_snapshot", sa.JSON(), nullable=True),
        sa.Column("cart_snapshot", sa.JSON(), nullable=True),
        sa.Column("total_price_snapshot", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_session_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_checkout_sessions_user_ref", "checkout_sessions", ["user_ref"])
    op.create_index("ix_checkout_sessions_order_id", "checkout_sessions", ["order_id"])

    op.add_column("orders", sa.Column("checkout_session_id", sa.BigInteger(), nullable=True))
    op.add_column("orders", sa.Column("source_session_id", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("payment_mode", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("address_snapshot", sa.JSON(), nullable=True))
    op.add_column("orders", sa.Column("cart_snapshot", sa.JSON(), nullable=True))
    op.add_column("orders", sa.Column("total_price_snapshot", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "total_price_snapshot")
    op.drop_column("orders", "cart_snapshot")
    op.drop_column("orders", "address_snapshot")
    op.drop_column("orders", "payment_mode")
    op.drop_column("orders", "source_session_id")
    op.drop_column("orders", "checkout_session_id")

    op.drop_index("ix_checkout_sessions_order_id", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_user_ref", table_name="checkout_sessions")
    op.drop_table("checkout_sessions")

    op.drop_index("ix_addresses_user_ref", table_name="addresses")
    op.drop_table("addresses")

    op.drop_index("ix_cart_items_product_id", table_name="cart_items")
    op.drop_index("ix_cart_items_cart_id", table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index("ix_carts_user_ref", table_name="carts")
    op.drop_table("carts")
