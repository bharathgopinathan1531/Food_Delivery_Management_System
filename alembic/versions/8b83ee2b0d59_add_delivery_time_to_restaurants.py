"""add delivery time to restaurants

Revision ID: 8b83ee2b0d59
Revises: ab5df7fc361c
Create Date: 2026-09-11 15:43:08.049844
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b83ee2b0d59"
down_revision: Union[str, None] = "ab5df7fc361c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    op.add_column(
        "restaurants",
        sa.Column(
            "delivery_time",
            sa.Integer(),
            nullable=False,
            server_default="30"
        )
    )

    op.alter_column(
        "restaurants",
        "delivery_time",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade database schema."""

    op.drop_column(
        "restaurants",
        "delivery_time"
    )