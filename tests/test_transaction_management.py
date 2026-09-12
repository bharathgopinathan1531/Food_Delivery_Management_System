import pytest
from sqlalchemy import text

from app.database import SessionLocal


def test_transaction_commit():
    """
    Verify that a database transaction can be committed
    successfully.
    """

    db = SessionLocal()

    try:
        db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS transaction_test "
                "(id INTEGER PRIMARY KEY, name VARCHAR(100))"
            )
        )

        db.execute(
            text(
                "INSERT INTO transaction_test (id, name) "
                "VALUES (1, 'Transaction Test')"
            )
        )

        db.commit()

        result = db.execute(
            text(
                "SELECT name FROM transaction_test "
                "WHERE id = 1"
            )
        ).scalar_one()

        assert result == "Transaction Test"

    finally:
        db.close()


def test_transaction_rollback():
    """
    Verify that a failed transaction can be rolled back
    without leaving uncommitted changes.
    """

    db = SessionLocal()

    try:
        db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS rollback_test "
                "(id INTEGER PRIMARY KEY, name VARCHAR(100))"
            )
        )

        db.commit()

        db.execute(
            text(
                "INSERT INTO rollback_test (id, name) "
                "VALUES (1, 'Rollback Test')"
            )
        )

        db.rollback()

        result = db.execute(
            text(
                "SELECT name FROM rollback_test "
                "WHERE id = 1"
            )
        ).scalar()

        assert result is None

    finally:
        db.close()


def test_transaction_failure_is_recoverable():
    """
    Verify that a failed transaction can be rolled back
    and the same session can continue working.
    """

    db = SessionLocal()

    try:
        db.execute(
            text(
                "CREATE TABLE IF NOT EXISTS recovery_test "
                "(id INTEGER PRIMARY KEY, name VARCHAR(100))"
            )
        )

        db.commit()

        with pytest.raises(Exception):

            db.execute(
                text(
                    "INSERT INTO recovery_test (id, name) "
                    "VALUES (1, 'First')"
                )
            )

            db.execute(
                text(
                    "INSERT INTO recovery_test (id, name) "
                    "VALUES (1, 'Duplicate')"
                )
            )

            db.commit()

        db.rollback()

        db.execute(
            text(
                "INSERT INTO recovery_test (id, name) "
                "VALUES (2, 'Recovered')"
            )
        )

        db.commit()

        result = db.execute(
            text(
                "SELECT name FROM recovery_test "
                "WHERE id = 2"
            )
        ).scalar_one()

        assert result == "Recovered"

    finally:
        db.close()