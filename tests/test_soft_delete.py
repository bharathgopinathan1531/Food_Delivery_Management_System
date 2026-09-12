from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.user import User
from app.repositories import restaurant_repository


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


def create_test_user(db, user_number):
    user = User(
        name=f"Test Admin {user_number}",
        email=f"softdelete{user_number}@example.com",
        password_hash="test-password",
        role="Admin",
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_test_restaurant(db, owner_id, restaurant_number):
    restaurant = Restaurant(
        restaurant_name=f"Soft Delete Restaurant {restaurant_number}",
        owner_id=owner_id,
        address="Test Address",
        city="Chennai",
        phone=f"987654{restaurant_number:04d}",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
        is_deleted=False,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


def test_restaurant_soft_delete():
    db = TestingSessionLocal()

    user = create_test_user(db, 1)

    restaurant = create_test_restaurant(
        db,
        user.id,
        1,
    )

    restaurant_repository.delete(
        db,
        restaurant,
    )

    assert restaurant.is_deleted is True

    db.close()


def test_soft_deleted_restaurant_still_exists_in_database():
    db = TestingSessionLocal()

    user = create_test_user(db, 2)

    restaurant = create_test_restaurant(
        db,
        user.id,
        2,
    )

    restaurant_repository.delete(
        db,
        restaurant,
    )

    stored_restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant.id
        )
        .first()
    )

    assert stored_restaurant is not None
    assert stored_restaurant.is_deleted is True

    db.close()


def test_soft_deleted_restaurant_not_returned_by_get_by_id():
    db = TestingSessionLocal()

    user = create_test_user(db, 3)

    restaurant = create_test_restaurant(
        db,
        user.id,
        3,
    )

    restaurant_repository.delete(
        db,
        restaurant,
    )

    result = restaurant_repository.get_by_id(
        db,
        restaurant.id,
    )

    assert result is None

    db.close()


def test_soft_deleted_restaurant_not_returned_by_get_all():
    db = TestingSessionLocal()

    user = create_test_user(db, 4)

    restaurant = create_test_restaurant(
        db,
        user.id,
        4,
    )

    restaurant_repository.delete(
        db,
        restaurant,
    )

    restaurants = restaurant_repository.get_all(db)

    restaurant_ids = [
        item.id
        for item in restaurants
    ]

    assert restaurant.id not in restaurant_ids

    db.close()