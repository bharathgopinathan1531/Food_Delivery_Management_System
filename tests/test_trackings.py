from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

from app.models.user import User
from app.models.customer import Customer, Address
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_tracking import OrderTracking


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
def customer(db):
    user = create_user(
        db,
        name="Customer User",
        email="customer@example.com",
        phone="9000000001",
        role="Customer",
    )

    customer = Customer(
        user_id=user.id,
        name="Bharath",
        email="bharath@example.com",
        phone="9000000011",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@pytest.fixture()
def address(db, customer):
    address = Address(
        customer_id=customer.id,
        address_line="12 Main Street",
        city="Chennai",
        pincode="600001",
        latitude=13.0827,
        longitude=80.2707,
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


@pytest.fixture()
def restaurant(db):
    owner = create_user(
        db,
        name="Restaurant Owner",
        email="owner@example.com",
        phone="9000000002",
        role="Restaurant Owner",
    )

    restaurant = Restaurant(
        restaurant_name="Test Restaurant",
        owner_id=owner.id,
        address="100 Food Street",
        city="Chennai",
        phone="9000000003",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


def create_order(
    db,
    customer,
    restaurant,
    address,
    status=OrderStatus.PENDING,
):
    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=0.0,
        total_amount=520.0,
        order_status=status,
        payment_status=PaymentStatus.PAID,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@pytest.fixture()
def order(
    db,
    customer,
    restaurant,
    address,
):
    return create_order(
        db,
        customer,
        restaurant,
        address,
    )


@pytest.fixture()
def delivered_order(
    db,
    customer,
    restaurant,
    address,
):
    return create_order(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.DELIVERED,
    )


@pytest.fixture()
def cancelled_order(
    db,
    customer,
    restaurant,
    address,
):
    return create_order(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.CANCELLED,
    )


def tracking_payload(
    status="Preparing",
    location="Chennai",
    remarks="Order is being prepared",
):
    return {
        "status": status,
        "location": location,
        "remarks": remarks,
    }


def test_create_tracking_record(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json=tracking_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order.id
    assert data["status"] == "Preparing"
    assert data["location"] == "Chennai"
    assert data["remarks"] == "Order is being prepared"
    assert data["timestamp"] is not None


def test_create_tracking_without_optional_fields(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Preparing"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order.id
    assert data["status"] == "Preparing"
    assert data["location"] is None
    assert data["remarks"] is None
    assert data["timestamp"] is not None


def test_create_tracking_order_not_found(
    client,
):
    response = client.post(
        "/orders/9999/tracking",
        json=tracking_payload(),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Order not found"


def test_delivered_order_tracking_rejected(
    client,
    delivered_order,
):
    response = client.post(
        f"/orders/{delivered_order.id}/tracking",
        json=tracking_payload(
            status="Delivered",
            location="Chennai",
            remarks="Delivered",
        ),
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Completed orders cannot receive tracking updates"
    )


def test_cancelled_order_tracking_rejected(
    client,
    cancelled_order,
):
    response = client.post(
        f"/orders/{cancelled_order.id}/tracking",
        json=tracking_payload(
            status="Cancelled",
            remarks="Order cancelled",
        ),
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Cancelled orders cannot receive tracking updates"
    )


def test_tracking_status_too_short(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "A"
        },
    )

    assert response.status_code == 422


def test_tracking_status_too_long(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "x" * 51
        },
    )

    assert response.status_code == 422


def test_tracking_location_max_length(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Preparing",
            "location": "x" * 255,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["location"] == "x" * 255


def test_tracking_location_over_max_length(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Preparing",
            "location": "x" * 256,
        },
    )

    assert response.status_code == 422


def test_tracking_remarks_max_length(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Preparing",
            "remarks": "x" * 500,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["remarks"] == "x" * 500


def test_tracking_remarks_over_max_length(
    client,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Preparing",
            "remarks": "x" * 501,
        },
    )

    assert response.status_code == 422


def test_get_tracking_history(
    client,
    order,
):
    first = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Pending",
            "location": "Restaurant",
            "remarks": "Order placed",
        },
    )

    second = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Preparing",
            "location": "Kitchen",
            "remarks": "Food is being prepared",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        f"/orders/{order.id}/tracking"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["status"] == "Pending"
    assert data[0]["location"] == "Restaurant"

    assert data[1]["status"] == "Preparing"
    assert data[1]["location"] == "Kitchen"


def test_get_tracking_history_empty(
    client,
    order,
):
    response = client.get(
        f"/orders/{order.id}/tracking"
    )

    assert response.status_code == 200

    assert response.json() == []


def test_get_tracking_history_order_not_found(
    client,
):
    response = client.get(
        "/orders/9999/tracking"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Order not found"


def test_multiple_tracking_updates(
    client,
    order,
):
    statuses = [
        "Pending",
        "Accepted",
        "Preparing",
        "Ready",
        "Picked Up",
        "Out for Delivery",
    ]

    for status in statuses:
        response = client.post(
            f"/orders/{order.id}/tracking",
            json={
                "status": status,
                "location": "Chennai",
                "remarks": f"Status updated to {status}",
            },
        )

        assert response.status_code == 201

    response = client.get(
        f"/orders/{order.id}/tracking"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == len(statuses)

    assert [
        item["status"]
        for item in data
    ] == statuses


def test_tracking_record_saved_in_database(
    client,
    db,
    order,
):
    response = client.post(
        f"/orders/{order.id}/tracking",
        json={
            "status": "Out for Delivery",
            "location": "Chennai",
            "remarks": "Driver has picked up the order",
        },
    )

    assert response.status_code == 201

    tracking_id = response.json()["id"]

    tracking = (
        db.query(OrderTracking)
        .filter(
            OrderTracking.id == tracking_id
        )
        .first()
    )

    assert tracking is not None
    assert tracking.order_id == order.id
    assert tracking.status == "Out for Delivery"
    assert tracking.location == "Chennai"
    assert (
        tracking.remarks
        == "Driver has picked up the order"
    )