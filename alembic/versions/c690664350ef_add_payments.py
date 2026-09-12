"""add payments

Revision ID: c690664350ef
Revises: 9414cc8505ef
Create Date: 2026-09-10 13:44:00.845762
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c690664350ef"
down_revision: Union[str, None] = "9414cc8505ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "payment_method",
            sa.Enum(
                "UPI",
                "CARD",
                "WALLET",
                "CASH_ON_DELIVERY",
                name="paymentmethod"
            ),
            nullable=False
        ),
        sa.Column(
            "transaction_id",
            sa.String(length=100),
            nullable=False
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "PENDING",
                "SUCCESS",
                "FAILED",
                name="paymentstatus"
            ),
            nullable=False
        ),
        sa.Column(
            "paid_at",
            sa.DateTime(),
            nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"]
        ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        op.f("ix_payments_id"),
        "payments",
        ["id"],
        unique=False
    )

    op.create_index(
        op.f("ix_payments_order_id"),
        "payments",
        ["order_id"],
        unique=True
    )

    op.create_index(
        op.f("ix_payments_transaction_id"),
        "payments",
        ["transaction_id"],
        unique=True
    )

    # SQLite NOTE:
    # Do NOT add the delivery_partner_id foreign key here.
    # It was already handled in the Level 8 migration workaround.
    # SQLite does not support adding this constraint directly.


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_index(
        op.f("ix_payments_transaction_id"),
        table_name="payments"
    )

    op.drop_index(
        op.f("ix_payments_order_id"),
        table_name="payments"
    )

    op.drop_index(
        op.f("ix_payments_id"),
        table_name="payments"
    )

    op.drop_table("payments")