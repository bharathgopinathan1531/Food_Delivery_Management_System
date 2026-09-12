"""Add reviews table

Revision ID: ab5df7fc361c
Revises: 527478497a95
Create Date: 2026-09-10 16:04:35.722845
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ab5df7fc361c"
down_revision: Union[str, None] = "527478497a95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("food_item_id", sa.Integer(), nullable=True),
        sa.Column("delivery_partner_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["delivery_partner_id"],
            ["delivery_partners.id"],
        ),
        sa.ForeignKeyConstraint(
            ["food_item_id"],
            ["menu_items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_reviews_customer_id"),
        "reviews",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_reviews_delivery_partner_id"),
        "reviews",
        ["delivery_partner_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_reviews_food_item_id"),
        "reviews",
        ["food_item_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_reviews_id"),
        "reviews",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_reviews_order_id"),
        "reviews",
        ["order_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_reviews_restaurant_id"),
        "reviews",
        ["restaurant_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index(
        op.f("ix_reviews_restaurant_id"),
        table_name="reviews",
    )

    op.drop_index(
        op.f("ix_reviews_order_id"),
        table_name="reviews",
    )

    op.drop_index(
        op.f("ix_reviews_id"),
        table_name="reviews",
    )

    op.drop_index(
        op.f("ix_reviews_food_item_id"),
        table_name="reviews",
    )

    op.drop_index(
        op.f("ix_reviews_delivery_partner_id"),
        table_name="reviews",
    )

    op.drop_index(
        op.f("ix_reviews_customer_id"),
        table_name="reviews",
    )

    op.drop_table("reviews")