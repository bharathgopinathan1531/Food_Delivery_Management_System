import pytest

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


# ============================================================
# TEST BASE
# ============================================================

TestBase = declarative_base()


# ============================================================
# TEST MODELS
# ============================================================

class UniqueUser(TestBase):
    __tablename__ = "unique_users"

    id = Column(
        Integer,
        primary_key=True
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )


class UniqueRestaurantStaff(TestBase):
    __tablename__ = "unique_restaurant_staff"

    id = Column(
        Integer,
        primary_key=True
    )

    restaurant_id = Column(
        Integer,
        nullable=False
    )

    user_id = Column(
        Integer,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "user_id",
            name="uq_test_restaurant_staff"
        ),
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
# TEST 1 — SINGLE COLUMN UNIQUE
# ============================================================

def test_unique_email_constraint(db):
    first_user = UniqueUser(
        email="unique@example.com"
    )

    db.add(first_user)
    db.commit()

    duplicate_user = UniqueUser(
        email="unique@example.com"
    )

    db.add(duplicate_user)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ============================================================
# TEST 2 — COMPOSITE UNIQUE CONSTRAINT
# ============================================================

def test_composite_unique_constraint(db):
    first_staff = UniqueRestaurantStaff(
        restaurant_id=1,
        user_id=1
    )

    db.add(first_staff)
    db.commit()

    duplicate_staff = UniqueRestaurantStaff(
        restaurant_id=1,
        user_id=1
    )

    db.add(duplicate_staff)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ============================================================
# TEST 3 — DIFFERENT COMBINATION IS ALLOWED
# ============================================================

def test_different_composite_values_are_allowed(db):
    first_staff = UniqueRestaurantStaff(
        restaurant_id=1,
        user_id=1
    )

    second_staff = UniqueRestaurantStaff(
        restaurant_id=1,
        user_id=2
    )

    db.add_all(
        [
            first_staff,
            second_staff
        ]
    )

    db.commit()

    staff_count = db.query(
        UniqueRestaurantStaff
    ).count()

    assert staff_count == 2