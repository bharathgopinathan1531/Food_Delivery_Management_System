from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db


def test_session_local_creates_session():
    db = SessionLocal()

    try:
        assert isinstance(db, Session)
    finally:
        db.close()


def test_session_is_closed_after_close():
    db = SessionLocal()

    db.close()

    assert db.is_active is True


def test_get_db_yields_session():
    db_generator = get_db()

    db = next(db_generator)

    try:
        assert isinstance(db, Session)
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass