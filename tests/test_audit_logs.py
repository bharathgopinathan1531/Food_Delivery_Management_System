from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.audit_log_service import create_audit_log


DATABASE_URL = "sqlite://"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base.metadata.create_all(bind=engine)


def create_test_user(db, user_id):
    user = User(
        id=user_id,
        name=f"Test User {user_id}",
        email=f"test{user_id}@example.com",
        password_hash="test-password",
        role="Admin",
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def test_create_audit_log():
    db = TestingSessionLocal()

    create_test_user(db, 1)

    audit_log = create_audit_log(
        db=db,
        user_id=1,
        action="CREATE",
        entity_type="Restaurant",
        entity_id=5,
        description="Restaurant created successfully",
    )

    assert audit_log.id is not None
    assert audit_log.user_id == 1
    assert audit_log.action == "CREATE"
    assert audit_log.entity_type == "Restaurant"
    assert audit_log.entity_id == 5
    assert audit_log.description == (
        "Restaurant created successfully"
    )
    assert isinstance(
        audit_log.created_at,
        datetime,
    )

    db.close()


def test_audit_log_is_persisted():
    db = TestingSessionLocal()

    create_test_user(db, 2)

    audit_log = AuditLog(
        user_id=2,
        action="UPDATE",
        entity_type="MenuItem",
        entity_id=10,
        description="Menu item updated",
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    saved_log = (
        db.query(AuditLog)
        .filter(AuditLog.id == audit_log.id)
        .first()
    )

    assert saved_log is not None
    assert saved_log.action == "UPDATE"
    assert saved_log.entity_type == "MenuItem"
    assert saved_log.entity_id == 10
    assert saved_log.user_id == 2

    db.close()


def test_audit_log_can_be_created_without_user():
    db = TestingSessionLocal()

    audit_log = AuditLog(
        user_id=None,
        action="SYSTEM",
        entity_type="System",
        entity_id=None,
        description="System generated audit entry",
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    assert audit_log.id is not None
    assert audit_log.user_id is None
    assert audit_log.action == "SYSTEM"
    assert audit_log.entity_type == "System"

    db.close()