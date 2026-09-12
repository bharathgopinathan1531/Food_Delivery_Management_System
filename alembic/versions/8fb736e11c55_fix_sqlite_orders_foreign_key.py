"""fix sqlite orders foreign key

Revision ID: 8fb736e11c55
Revises: 46af3b4e8235
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "8fb736e11c55"

down_revision: Union[str, None] = "46af3b4e8235"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """
    Fix the SQLite orders table schema.
    """

    bind = op.get_bind()

    inspector = sa.inspect(bind)

    # ========================================================
    # REMOVE LEFTOVER ALEMBIC TEMPORARY TABLE
    # ========================================================

    if "_alembic_tmp_orders" in inspector.get_table_names():

        op.execute(
            "DROP TABLE _alembic_tmp_orders"
        )

    # ========================================================
    # CHECK ORDERS FOREIGN KEYS
    # ========================================================

    inspector = sa.inspect(bind)

    foreign_keys = inspector.get_foreign_keys(
        "orders"
    )

    delivery_partner_fk_exists = any(
        "delivery_partner_id"
        in fk.get(
            "constrained_columns",
            []
        )
        and fk.get(
            "referred_table"
        ) == "delivery_partners"
        for fk in foreign_keys
    )

    # ========================================================
    # ADD DELIVERY PARTNER FOREIGN KEY
    # ========================================================

    if not delivery_partner_fk_exists:

        with op.batch_alter_table(
            "orders",
            schema=None,
            recreate="always"
        ) as batch_op:

            batch_op.create_foreign_key(
                "fk_orders_delivery_partner_id",
                "delivery_partners",
                ["delivery_partner_id"],
                ["id"]
            )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Remove the delivery partner foreign key.
    """

    bind = op.get_bind()

    inspector = sa.inspect(bind)

    foreign_keys = inspector.get_foreign_keys(
        "orders"
    )

    delivery_partner_fk = next(
        (
            fk
            for fk in foreign_keys
            if "delivery_partner_id"
            in fk.get(
                "constrained_columns",
                []
            )
            and fk.get(
                "referred_table"
            ) == "delivery_partners"
        ),
        None
    )

    if delivery_partner_fk:

        constraint_name = delivery_partner_fk.get(
            "name"
        )

        if constraint_name:

            with op.batch_alter_table(
                "orders",
                schema=None,
                recreate="always"
            ) as batch_op:

                batch_op.drop_constraint(
                    constraint_name,
                    type_="foreignkey"
                )