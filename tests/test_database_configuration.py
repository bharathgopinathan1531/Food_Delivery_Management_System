from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.config import settings
from app.database import engine, SessionLocal


def test_database_url_is_configured():
    assert settings.DATABASE_URL
    assert (
        settings.DATABASE_URL.startswith("sqlite")
        or settings.DATABASE_URL.startswith("postgresql")
    )


def test_database_url_is_supported():
    url = make_url(settings.DATABASE_URL)

    assert url.drivername in {
        "sqlite",
        "postgresql",
        "postgresql+psycopg2",
        "postgresql+psycopg",
    }


def test_database_engine_is_created():
    assert engine is not None
    assert engine.url.drivername in {
        "sqlite",
        "postgresql",
        "postgresql+psycopg2",
        "postgresql+psycopg",
    }


def test_sqlite_configuration():
    if settings.DATABASE_URL.startswith("sqlite"):
        assert engine.url.drivername == "sqlite"
        assert engine.url.database


def test_session_factory_is_bound_to_engine():
    session = SessionLocal()

    try:
        assert session.bind is engine
    finally:
        session.close()