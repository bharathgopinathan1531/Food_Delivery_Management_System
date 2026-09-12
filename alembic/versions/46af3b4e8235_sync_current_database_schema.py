"""sync current database schema

Revision ID: 46af3b4e8235
Revises: 8b83ee2b0d59
Create Date: 2026-09-12 11:35:44.611381
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "46af3b4e8235"

down_revision: Union[str, None] = "8b83ee2b0d59"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """
    Synchronize the existing SQLite database with the
    current SQLAlchemy models.
    """

    bind = op.get_bind()

    inspector = sa.inspect(bind)


    # ========================================================
    # 1. REMOVE LEFTOVER ALEMBIC TEMPORARY TABLE
    # ========================================================
    #
    # A previous failed batch migration left this table behind.
    #
    # It is NOT part of the application schema.
    #
    # ========================================================

    if "_alembic_tmp_orders" in inspector.get_table_names():

        op.execute(
            "DROP TABLE _alembic_tmp_orders"
        )


    # ========================================================
    # 2. AUDIT LOGS TABLE
    # ========================================================

    inspector = sa.inspect(bind)

    if "audit_logs" not in inspector.get_table_names():

        op.create_table(
            "audit_logs",

            sa.Column(
                "id",
                sa.Integer(),
                nullable=False
            ),

            sa.Column(
                "user_id",
                sa.Integer(),
                nullable=True
            ),

            sa.Column(
                "action",
                sa.String(length=50),
                nullable=False
            ),

            sa.Column(
                "entity_type",
                sa.String(length=100),
                nullable=False
            ),

            sa.Column(
                "entity_id",
                sa.Integer(),
                nullable=True
            ),

            sa.Column(
                "description",
                sa.Text(),
                nullable=True
            ),

            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False
            ),

            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"]
            ),

            sa.PrimaryKeyConstraint(
                "id"
            )
        )


    # ========================================================
    # 3. AUDIT LOGS INDEX
    # ========================================================

    inspector = sa.inspect(bind)

    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes(
            "audit_logs"
        )
    }

    if "ix_audit_logs_id" not in existing_indexes:

        op.create_index(
            "ix_audit_logs_id",
            "audit_logs",
            ["id"],
            unique=False
        )


    # ========================================================
    # 4. ORDERS DELIVERY PARTNER FOREIGN KEY
    # ========================================================
    #
    # SQLite requires a table rebuild to add a foreign key.
    #
    # Other tables reference orders, so SQLite foreign-key
    # enforcement must be temporarily disabled while the
    # table is rebuilt.
    #
    # The temporary table is removed first above.
    #
    # ========================================================

    inspector = sa.inspect(bind)

    orders_foreign_keys = inspector.get_foreign_keys(
        "orders"
    )

    delivery_partner_fk_exists = any(
        "delivery_partner_id" in fk.get(
            "constrained_columns",
            []
        )
        and fk.get(
            "referred_table"
        ) == "delivery_partners"
        for fk in orders_foreign_keys
    )


    if not delivery_partner_fk_exists:

        # Temporarily disable SQLite FK checks so that
        # Alembic can safely rebuild the orders table.

        op.execute(
            "PRAGMA foreign_keys=OFF"
        )

        try:

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

        finally:

            op.execute(
                "PRAGMA foreign_keys=ON"
            )


    # ========================================================
    # 5. PAYMENT STATUS
    # ========================================================
    #
    # SQLite stores SQLAlchemy Enum as VARCHAR.
    #
    # env.py intentionally disables type comparison for
    # SQLite because VARCHAR <-> Enum is not a meaningful
    # physical schema difference on SQLite.
    #
    # Therefore no ALTER operation is required here.
    #
    # ========================================================


    # ========================================================
    # 6. RESTAURANT SOFT DELETE
    # ========================================================

    inspector = sa.inspect(bind)

    restaurant_columns = {
        column["name"]
        for column in inspector.get_columns(
            "restaurants"
        )
    }


    if "is_deleted" not in restaurant_columns:

        op.add_column(
            "restaurants",

            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

        # Do NOT remove the server default.
        #
        # SQLite does not support:
        #
        # ALTER TABLE ... ALTER COLUMN ... DROP DEFAULT
        #
        # Keeping it is SQLite-safe.


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Reverse the schema synchronization.
    """

    bind = op.get_bind()

    inspector = sa.inspect(bind)


    # ========================================================
    # 1. REMOVE RESTAURANT SOFT DELETE
    # ========================================================

    restaurant_columns = {
        column["name"]
        for column in inspector.get_columns(
            "restaurants"
        )
    }


    if "is_deleted" in restaurant_columns:

        op.drop_column(
            "restaurants",
            "is_deleted"
        )


    # ========================================================
    # 2. REMOVE ORDERS DELIVERY PARTNER FOREIGN KEY
    # ========================================================

    inspector = sa.inspect(bind)

    orders_foreign_keys = inspector.get_foreign_keys(
        "orders"
    )


    delivery_partner_fk = next(
        (
            fk
            for fk in orders_foreign_keys
            if "delivery_partner_id" in fk.get(
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

        op.execute(
            "PRAGMA foreign_keys=OFF"
        )

        try:

            with op.batch_alter_table(
                "orders",
                schema=None,
                recreate="always"
            ) as batch_op:

                batch_op.drop_constraint(
                    delivery_partner_fk["name"],
                    type_="foreignkey"
                )

        finally:

            op.execute(
                "PRAGMA foreign_keys=ON"
            )


    # ========================================================
    # 3. REMOVE AUDIT LOGS INDEX
    # ========================================================

    inspector = sa.inspect(bind)

    if "audit_logs" in inspector.get_table_names():

        existing_indexes = {
            index["name"]
            for index in inspector.get_indexes(
                "audit_logs"
            )
        }

        if "ix_audit_logs_id" in existing_indexes:

            op.drop_index(
                "ix_audit_logs_id",
                table_name="audit_logs"
            )


    # ========================================================
    # 4. REMOVE AUDIT LOGS TABLE
    # ========================================================

    inspector = sa.inspect(bind)

    if "audit_logs" in inspector.get_table_names():

        op.drop_table(
            "audit_logs"
        )