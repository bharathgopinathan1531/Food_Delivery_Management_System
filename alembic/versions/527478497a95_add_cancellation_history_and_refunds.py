"""add cancellation history and refunds

Revision ID: 527478497a95
Revises: c690664350ef
Create Date: 2026-09-10 14:53:17.464861
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "527478497a95"
down_revision: Union[str, None] = "c690664350ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "cancellation_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column(
            "previous_status",
            sa.String(length=50),
            nullable=False
        ),
        sa.Column(
            "cancellation_reason",
            sa.String(length=500),
            nullable=True
        ),
        sa.Column(
            "refund_amount",
            sa.Float(),
            nullable=False,
            default=0.0
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"]
        ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        op.f("ix_cancellation_history_id"),
        "cancellation_history",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_cancellation_history_order_id"),
        "cancellation_history",
        ["order_id"],
        unique=False
    )

    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "refund_status",
            sa.String(length=30),
            nullable=False,
            default="Success"
        ),
        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=True
        ),
        sa.Column(
            "refunded_at",
            sa.DateTime(),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payments.id"]
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"]
        ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        op.f("ix_refunds_id"),
        "refunds",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_refunds_order_id"),
        "refunds",
        ["order_id"],
        unique=False
    )

    op.create_index(
        op.f("ix_refunds_payment_id"),
        "refunds",
        ["payment_id"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index(
        op.f("ix_refunds_payment_id"),
        table_name="refunds"
    )

    op.drop_index(
        op.f("ix_refunds_order_id"),
        table_name="refunds"
    )

    op.drop_index(
        op.f("ix_refunds_id"),
        table_name="refunds"
    )

    op.drop_table("refunds")

    op.drop_index(
        op.f("ix_cancellation_history_order_id"),
        table_name="cancellation_history"
    )

    op.drop_index(
        op.f("ix_cancellation_history_id"),
        table_name="cancellation_history"
    )

    op.drop_table("cancellation_history")