import pytest

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ============================================================
# TEST DATABASE
# ============================================================

@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False
        },
        poolclass=StaticPool,
    )

    # Enable SQLite foreign-key enforcement.
    @event.listens_for(
        engine,
        "connect"
    )
    def enable_foreign_keys(
        dbapi_connection,
        connection_record
    ):
        cursor = dbapi_connection.cursor()

        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

        cursor.close()

    connection = engine.connect()

    # Parent table.
    connection.execute(
        text(
            """
            CREATE TABLE parent (
                id INTEGER PRIMARY KEY
            )
            """
        )
    )

    # Child table with a foreign key.
    connection.execute(
        text(
            """
            CREATE TABLE child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER NOT NULL,
                FOREIGN KEY (parent_id)
                    REFERENCES parent(id)
            )
            """
        )
    )

    connection.commit()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()
        connection.close()
        engine.dispose()


# ============================================================
# TEST 1
# ============================================================

def test_foreign_keys_are_enabled(db):
    result = db.execute(
        text("PRAGMA foreign_keys")
    ).scalar()

    assert result == 1


# ============================================================
# TEST 2
# ============================================================

def test_invalid_foreign_key_is_rejected(db):
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                """
                INSERT INTO child (id, parent_id)
                VALUES (1, 999999)
                """
            )
        )

    db.rollback()