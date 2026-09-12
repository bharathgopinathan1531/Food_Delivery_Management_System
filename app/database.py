from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

connect_args = {}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


# ============================================================
# SQLITE FOREIGN KEY ENFORCEMENT
# ============================================================

@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record
):
    """
    Enable foreign-key constraint enforcement for SQLite.

    PostgreSQL enforces foreign keys by default, so this
    specifically ensures SQLite behaves correctly as well.
    """

    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()

        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

        cursor.close()


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================================
# BASE MODEL
# ============================================================

Base = declarative_base()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()