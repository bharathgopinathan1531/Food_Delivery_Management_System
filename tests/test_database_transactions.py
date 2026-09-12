import pytest

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


# ============================================================
# TEST DATABASE BASE
# ============================================================

TestBase = declarative_base()


# ============================================================
# TEST MODEL
# ============================================================

class TransactionTestRecord(TestBase):
    __tablename__ = "transaction_test_records"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String(100),
        nullable=False
    )


# ============================================================
# DATABASE FIXTURE
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

    TestBase.metadata.create_all(
        bind=engine
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        TestBase.metadata.drop_all(
            bind=engine
        )

        engine.dispose()


# ============================================================
# TEST 1 — SUCCESSFUL TRANSACTION COMMIT
# ============================================================

def test_transaction_commit(db):
    record = TransactionTestRecord(
        name="Committed Record"
    )

    db.add(record)
    db.commit()

    saved_record = (
        db.query(TransactionTestRecord)
        .filter(
            TransactionTestRecord.name
            == "Committed Record"
        )
        .first()
    )

    assert saved_record is not None
    assert saved_record.name == "Committed Record"


# ============================================================
# TEST 2 — TRANSACTION ROLLBACK
# ============================================================

def test_transaction_rollback(db):
    first_record = TransactionTestRecord(
        name="First Record"
    )

    db.add(first_record)
    db.flush()

    duplicate_record = TransactionTestRecord(
        id=first_record.id,
        name="Duplicate Record"
    )

    db.add(duplicate_record)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()

    records = (
        db.query(TransactionTestRecord)
        .all()
    )

    assert records == []


# ============================================================
# TEST 3 — ROLLBACK ALLOWS NEW TRANSACTION
# ============================================================

def test_new_transaction_after_rollback(db):
    first_record = TransactionTestRecord(
        name="Failed Transaction"
    )

    db.add(first_record)
    db.flush()

    duplicate_record = TransactionTestRecord(
        id=first_record.id,
        name="Duplicate Record"
    )

    db.add(duplicate_record)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()

    valid_record = TransactionTestRecord(
        name="Successful Transaction"
    )

    db.add(valid_record)
    db.commit()

    saved_record = (
        db.query(TransactionTestRecord)
        .filter(
            TransactionTestRecord.name
            == "Successful Transaction"
        )
        .first()
    )

    assert saved_record is not None
    assert saved_record.name == "Successful Transaction"