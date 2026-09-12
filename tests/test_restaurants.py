from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStatus
from app.utils.dependencies import get_current_user


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False
        },
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_user(
    db,
    name="Test User",
    email="user@example.com",
    phone="9876543210",
    role="Customer",
):
    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash="hashed-password",
        role=role,
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def admin(db):
    return create_user(
        db,
        name="Admin User",
        email="admin@example.com",
        phone="9000000001",
        role="Admin",
    )


@pytest.fixture()
def owner(db):
    return create_user(
        db,
        name="Restaurant Owner",
        email="owner@example.com",
        phone="9000000002",
        role="Restaurant Owner",
    )


@pytest.fixture()
def second_owner(db):
    return create_user(
        db,
        name="Second Owner",
        email="owner2@example.com",
        phone="9000000003",
        role="Restaurant Owner",
    )


@pytest.fixture()
def customer(db):
    return create_user(
        db,
        name="Customer User",
        email="customer@example.com",
        phone="9000000004",
        role="Customer",
    )


def authenticate_as(user):
    app.dependency_overrides[get_current_user] = (
        lambda: user
    )


def restaurant_payload(owner_id, **overrides):
    payload = {
        "restaurant_name": "Test Restaurant",
        "owner_id": owner_id,
        "address": "100 Food Street",
        "city": "Chennai",
        "phone": "9000000010",
        "cuisine_type": "Indian",
        "opening_time": "09:00:00",
        "closing_time": "22:00:00",
        "status": "Open",
        "delivery_radius": 10.0,
        "delivery_time": 30,
    }

    payload.update(overrides)

    return payload


def create_restaurant(
    db,
    owner_id,
    restaurant_name="Test Restaurant",
    city="Chennai",
    cuisine_type="Indian",
    delivery_time=30,
    status=RestaurantStatus.OPEN,
):
    restaurant = Restaurant(
        restaurant_name=restaurant_name,
        owner_id=owner_id,
        address="100 Food Street",
        city=city,
        phone="9000000010",
        cuisine_type=cuisine_type,
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=status,
        delivery_radius=10.0,
        delivery_time=delivery_time,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


def test_create_restaurant_as_admin(
    client,
    admin,
    owner,
):
    authenticate_as(admin)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(owner.id),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_name"] == "Test Restaurant"
    assert data["owner_id"] == owner.id
    assert data["address"] == "100 Food Street"
    assert data["city"] == "Chennai"
    assert data["phone"] == "9000000010"
    assert data["cuisine_type"] == "Indian"
    assert data["opening_time"] == "09:00:00"
    assert data["closing_time"] == "22:00:00"
    assert data["status"] == "Open"
    assert data["delivery_radius"] == 10.0
    assert data["delivery_time"] == 30


def test_create_restaurant_as_owner(
    client,
    owner,
):
    authenticate_as(owner)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(owner.id),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["owner_id"] == owner.id


def test_owner_cannot_create_restaurant_for_another_owner(
    client,
    owner,
    second_owner,
):
    authenticate_as(owner)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(second_owner.id),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Restaurant owners can create restaurants only for themselves"
    )


def test_customer_cannot_create_restaurant(
    client,
    customer,
    owner,
):
    authenticate_as(customer)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(owner.id),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == "Insufficient permissions"


def test_create_restaurant_owner_not_found(
    client,
    admin,
):
    authenticate_as(admin)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(9999),
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Restaurant owner not found"
    )


def test_create_restaurant_invalid_owner_role(
    client,
    admin,
    customer,
):
    authenticate_as(admin)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(customer.id),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Only restaurant owners or admins can create restaurants"
    )


def test_create_restaurant_invalid_closing_time(
    client,
    admin,
    owner,
):
    authenticate_as(admin)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(
            owner.id,
            opening_time="22:00:00",
            closing_time="09:00:00",
        ),
    )

    assert response.status_code == 422


def test_create_restaurant_invalid_delivery_radius(
    client,
    admin,
    owner,
):
    authenticate_as(admin)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(
            owner.id,
            delivery_radius=0,
        ),
    )

    assert response.status_code == 422


def test_create_restaurant_invalid_delivery_time(
    client,
    admin,
    owner,
):
    authenticate_as(admin)

    response = client.post(
        "/restaurants",
        json=restaurant_payload(
            owner.id,
            delivery_time=0,
        ),
    )

    assert response.status_code == 422


def test_get_all_restaurants(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    restaurant1 = create_restaurant(
        db,
        owner.id,
        restaurant_name="Restaurant One",
    )

    restaurant2 = create_restaurant(
        db,
        owner.id,
        restaurant_name="Restaurant Two",
    )

    response = client.get("/restaurants")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["id"] == restaurant2.id
    assert data[1]["id"] == restaurant1.id


def test_get_all_restaurants_requires_authentication(
    client,
):
    response = client.get("/restaurants")

    assert response.status_code == 401


def test_get_restaurant(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    restaurant = create_restaurant(
        db,
        owner.id,
    )

    response = client.get(
        f"/restaurants/{restaurant.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == restaurant.id
    assert data["restaurant_name"] == "Test Restaurant"
    assert data["owner_id"] == owner.id


def test_get_restaurant_not_found(
    client,
    admin,
):
    authenticate_as(admin)

    response = client.get(
        "/restaurants/9999"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Restaurant not found"
    )


def test_search_restaurants_by_city(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Chennai Restaurant",
        city="Chennai",
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Madurai Restaurant",
        city="Madurai",
    )

    response = client.get(
        "/restaurants/search",
        params={
            "city": "Chennai",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["city"] == "Chennai"


def test_search_restaurants_by_cuisine(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Indian Restaurant",
        cuisine_type="Indian",
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Chinese Restaurant",
        cuisine_type="Chinese",
    )

    response = client.get(
        "/restaurants/search",
        params={
            "cuisine": "Indian",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["cuisine_type"] == "Indian"


def test_search_restaurants_by_delivery_time(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Fast Restaurant",
        delivery_time=20,
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Slow Restaurant",
        delivery_time=45,
    )

    response = client.get(
        "/restaurants/search",
        params={
            "delivery_time": 30,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_name"] == "Fast Restaurant"


def test_search_restaurants_by_status(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Open Restaurant",
        status=RestaurantStatus.OPEN,
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Busy Restaurant",
        status=RestaurantStatus.BUSY,
    )

    response = client.get(
        "/restaurants/search",
        params={
            "status": "Open",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_name"] == "Open Restaurant"


def test_search_restaurants_pagination(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Restaurant One",
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Restaurant Two",
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Restaurant Three",
    )

    response = client.get(
        "/restaurants/search",
        params={
            "page": 1,
            "limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_search_restaurants_sort_by_name_ascending(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Zeta Restaurant",
    )

    create_restaurant(
        db,
        owner.id,
        restaurant_name="Alpha Restaurant",
    )

    response = client.get(
        "/restaurants/search",
        params={
            "sort_by": "name",
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data[0]["restaurant_name"] == "Alpha Restaurant"
    assert data[1]["restaurant_name"] == "Zeta Restaurant"


def test_update_restaurant_as_admin(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    restaurant = create_restaurant(
        db,
        owner.id,
    )

    response = client.put(
        f"/restaurants/{restaurant.id}",
        json={
            "restaurant_name": "Updated Restaurant",
            "city": "Bangalore",
            "delivery_time": 25,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_name"] == "Updated Restaurant"
    assert data["city"] == "Bangalore"
    assert data["delivery_time"] == 25


def test_update_restaurant_as_owner(
    client,
    db,
    owner,
):
    authenticate_as(owner)

    restaurant = create_restaurant(
        db,
        owner.id,
    )

    response = client.put(
        f"/restaurants/{restaurant.id}",
        json={
            "restaurant_name": "Owner Updated Restaurant",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["restaurant_name"]
        == "Owner Updated Restaurant"
    )


def test_owner_cannot_update_another_restaurant(
    client,
    db,
    owner,
    second_owner,
):
    authenticate_as(owner)

    restaurant = create_restaurant(
        db,
        second_owner.id,
    )

    response = client.put(
        f"/restaurants/{restaurant.id}",
        json={
            "restaurant_name": "Unauthorized Update",
        },
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can update only your own restaurant"
    )


def test_update_restaurant_invalid_time(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    restaurant = create_restaurant(
        db,
        owner.id,
    )

    response = client.put(
        f"/restaurants/{restaurant.id}",
        json={
            "opening_time": "20:00:00",
            "closing_time": "10:00:00",
        },
    )

    assert response.status_code == 422

    assert (
        response.json()["detail"]
        == "Closing time must be later than opening time"
    )


def test_update_restaurant_not_found(
    client,
    admin,
):
    authenticate_as(admin)

    response = client.put(
        "/restaurants/9999",
        json={
            "restaurant_name": "Updated Restaurant",
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Restaurant not found"
    )


def test_delete_restaurant_as_admin(
    client,
    db,
    admin,
    owner,
):
    authenticate_as(admin)

    restaurant = create_restaurant(
        db,
        owner.id,
    )

    response = client.delete(
        f"/restaurants/{restaurant.id}"
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Restaurant deleted successfully"
    )

    deleted = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant.id
        )
        .first()
    )

    assert deleted is not None
    assert deleted.is_deleted is True


def test_owner_cannot_delete_another_restaurant(
    client,
    db,
    owner,
    second_owner,
):
    authenticate_as(owner)

    restaurant = create_restaurant(
        db,
        second_owner.id,
    )

    response = client.delete(
        f"/restaurants/{restaurant.id}"
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can delete only your own restaurant"
    )


def test_delete_restaurant_not_found(
    client,
    admin,
):
    authenticate_as(admin)

    response = client.delete(
        "/restaurants/9999"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Restaurant not found"
    )