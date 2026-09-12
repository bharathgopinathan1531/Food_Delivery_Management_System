from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(
    db: Session,
    email: str
):
    return (
        db.query(User)
        .filter(
            User.email == email,
            User.is_deleted == False
        )
        .first()
    )


def get_by_id(
    db: Session,
    user_id: int
):
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_deleted == False
        )
        .first()
    )


def create(
    db: Session,
    user: User
):

    db.add(user)
    db.commit()
    db.refresh(user)

    return user