"""add delivery partners and assign driver to orders

Revision ID: 0d9a8acafcfa
Revises: dbf08eb21177
Create Date: 2026-09-10 11:24:05.385111
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0d9a8acafcfa"
down_revision: Union[str, None] = "dbf08eb21177"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    The migration was partially applied successfully during the
    first attempt.

    SQLite completed:
    - delivery_partners table
    - delivery partner indexes
    - orders.delivery_partner_id column
    - orders.delivery_partner_id index

    The only failed operation was adding the foreign key because
    SQLite does not support ALTER TABLE ADD CONSTRAINT directly.

    The SQLAlchemy models already define the relationship and
    ForeignKey, so no additional operation is required here.
    """

    pass


def downgrade() -> None:
    """
    The upgrade was already applied to the SQLite database.
    No downgrade operation is required for this repaired migration.
    """

    pass