"""add order tracking

Revision ID: 9414cc8505ef
Revises: 0d9a8acafcfa
Create Date: 2026-09-10 12:26:32.845058
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9414cc8505ef"
down_revision: Union[str, None] = "0d9a8acafcfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    # ---------------------------------------------------------
    # 1. Create order_tracking table
    # ---------------------------------------------------------
    op.create_table(
        "order_tracking",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "order_id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False
        ),
        sa.Column(
            "location",
            sa.String(length=255),
            nullable=True
        ),
        sa.Column(
            "remarks",
            sa.String(length=500),
            nullable=True
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"]
        ),
        sa.PrimaryKeyConstraint("id")
    )

    # ---------------------------------------------------------
    # 2. Create order tracking indexes
    # ---------------------------------------------------------
    op.create_index(
        op.f("ix_order_tracking_id"),
        "order_tracking",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_order_tracking_order_id"),
        "order_tracking",
        ["order_id"],
        unique=False
    )

    # ---------------------------------------------------------
    # SQLite NOTE:
    #
    # Do NOT add the delivery_partner_id foreign key here.
    # It was already handled by the Level 8 SQLite migration.
    # SQLite does not support ALTER TABLE ADD CONSTRAINT.
    # ---------------------------------------------------------


def downgrade() -> None:
    """Downgrade database schema."""

    # ---------------------------------------------------------
    # 1. Remove order tracking indexes
    # ---------------------------------------------------------
    op.drop_index(
        op.f("ix_order_tracking_order_id"),
        table_name="order_tracking"
    )

    op.drop_index(
        op.f("ix_order_tracking_id"),
        table_name="order_tracking"
    )

    # ---------------------------------------------------------
    # 2. Remove order_tracking table
    # ---------------------------------------------------------
    op.drop_table(
        "order_tracking"
    )