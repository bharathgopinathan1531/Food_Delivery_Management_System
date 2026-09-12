from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.config import settings
from app.database import Base
from app.models import *


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = context.config


if config.config_file_name is not None:
    fileConfig(
        config.config_file_name
    )


# ============================================================
# TARGET METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# DATABASE URL
# ============================================================

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace(
        "%",
        "%%"
    )
)


# ============================================================
# MIGRATION CONFIGURATION
# ============================================================

def get_migration_config():

    # SQLite represents SQLAlchemy Enum values as VARCHAR.
    #
    # Therefore do not report Enum/VARCHAR as a schema
    # difference when using SQLite.

    if settings.DATABASE_URL.startswith("sqlite"):

        return {
            "compare_type": False
        }

    return {
        "compare_type": True
    }


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    migration_config = get_migration_config()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        **migration_config
    )

    with context.begin_transaction():

        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        is_sqlite = settings.DATABASE_URL.startswith(
            "sqlite"
        )

        # ----------------------------------------------------
        # SQLite FK handling
        # ----------------------------------------------------
        #
        # SQLite needs foreign_keys=OFF while Alembic
        # rebuilds the orders table.
        #
        # This is done BEFORE Alembic starts its transaction.
        #
        # ----------------------------------------------------

        if is_sqlite:

            connection.exec_driver_sql(
                "PRAGMA foreign_keys=OFF"
            )


        migration_config = get_migration_config()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **migration_config
        )


        try:

            with context.begin_transaction():

                context.run_migrations()

        finally:

            if is_sqlite:

                connection.exec_driver_sql(
                    "PRAGMA foreign_keys=ON"
                )


# ============================================================
# RUN MIGRATIONS
# ============================================================

if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()