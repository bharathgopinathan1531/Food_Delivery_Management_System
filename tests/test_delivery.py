import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

from app.models.user import User
from app.models.customer import Customer, Address
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.menu import MenuItem, SpicyLevel
from app.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerStatus,
)
from app.models.order import (
    Order,
    OrderStatus,
    PaymentStatus,
)
from app.models.order_tracking import OrderTracking


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user():
    db = TestingSessionLocal()

    user = User(
        name="Delivery Test User",
        email="deliveryuser@gmail.com",
        phone="9876543210",
        password_hash="hashed_password",
        role="Customer",
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    db.close()

    return user


@pytest.fixture
def customer(user):
    db = TestingSessionLocal()

    customer = Customer(
        user_id=user.id,
        name="Delivery Customer",
        email="deliverycustomer@gmail.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    db.close()

    return customer


@pytest.fixture
def address(customer):
    db = TestingSessionLocal()

    address = Address(
        customer_id=customer.id,
        address_line="123 Main Street",
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

    db.close()

    return address


@pytest.fixture
def restaurant(user):
    db = TestingSessionLocal()

    restaurant = Restaurant(
        restaurant_name="Delivery Restaurant",
        owner_id=user.id,
        address="456 Restaurant Road",
        city="Chennai",
        phone="9123456789",
        cuisine_type="Indian",
        opening_time=__import__("datetime").time(9, 0),
        closing_time=__import__("datetime").time(23, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    db.close()

    return restaurant


@pytest.fixture
def menu_item(restaurant):
    db = TestingSessionLocal()

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Burger",
        description="Chicken burger",
        price=200.0,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    db.close()

    return item


@pytest.fixture
def delivery_partner_payload():
    return {
        "name": "Delivery Partner",
        "phone": "9000000001",
        "vehicle_type": "Bike",
        "vehicle_number": "TN01AB1234",
        "current_location": "Chennai",
    }


@pytest.fixture
def delivery_partner(
    client,
    delivery_partner_payload,
):

    response = client.post(
        "/delivery-partners",
        json=delivery_partner_payload,
    )

    assert response.status_code == 201

    return response.json()


@pytest.fixture
def order(
    customer,
    restaurant,
    address,
    menu_item,
):

    db = TestingSessionLocal()

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=400.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=20.0,
        total_amount=460.0,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    db.close()

    return order


def test_create_delivery_partner(
    client,
    delivery_partner_payload,
):

    response = client.post(
        "/delivery-partners",
        json=delivery_partner_payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["name"] == "Delivery Partner"
    assert data["phone"] == "9000000001"
    assert data["vehicle_type"] == "Bike"
    assert data["vehicle_number"] == "TN01AB1234"
    assert data["availability_status"] == "Available"
    assert data["current_location"] == "Chennai"


def test_create_delivery_partner_without_location(
    client,
):

    payload = {
        "name": "Partner Without Location",
        "phone": "9000000002",
        "vehicle_type": "Bike",
        "vehicle_number": "TN02CD5678",
    }

    response = client.post(
        "/delivery-partners",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Partner Without Location"
    assert data["availability_status"] == "Available"
    assert data["current_location"] is None


def test_get_delivery_partners(
    client,
    delivery_partner_payload,
):

    first_response = client.post(
        "/delivery-partners",
        json=delivery_partner_payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/delivery-partners",
        json={
            "name": "Second Partner",
            "phone": "9000000003",
            "vehicle_type": "Scooter",
            "vehicle_number": "TN03EF9012",
            "current_location": "Tambaram",
        },
    )

    assert second_response.status_code == 201

    response = client.get(
        "/delivery-partners"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    assert data[0]["id"] > data[1]["id"]


def test_duplicate_delivery_partner_phone(
    client,
    delivery_partner_payload,
):

    first_response = client.post(
        "/delivery-partners",
        json=delivery_partner_payload,
    )

    assert first_response.status_code == 201

    duplicate_payload = {
        "name": "Another Partner",
        "phone": "9000000001",
        "vehicle_type": "Car",
        "vehicle_number": "TN10XY1111",
        "current_location": "Chennai",
    }

    response = client.post(
        "/delivery-partners",
        json=duplicate_payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Delivery partner with this phone already exists"
    )


def test_duplicate_delivery_partner_vehicle_number(
    client,
    delivery_partner_payload,
):

    first_response = client.post(
        "/delivery-partners",
        json=delivery_partner_payload,
    )

    assert first_response.status_code == 201

    duplicate_payload = {
        "name": "Another Partner",
        "phone": "9000000004",
        "vehicle_type": "Car",
        "vehicle_number": "TN01AB1234",
        "current_location": "Chennai",
    }

    response = client.post(
        "/delivery-partners",
        json=duplicate_payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Delivery partner with this vehicle number already exists"
    )


def test_update_delivery_partner_status_to_busy(
    client,
    delivery_partner,
):

    partner_id = delivery_partner["id"]

    response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Busy"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == partner_id
    assert data["availability_status"] == "Busy"


def test_update_delivery_partner_status_to_offline(
    client,
    delivery_partner,
):

    partner_id = delivery_partner["id"]

    response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Offline"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["availability_status"] == "Offline"


def test_update_delivery_partner_status_to_available(
    client,
    delivery_partner,
):

    partner_id = delivery_partner["id"]

    busy_response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Busy"
        },
    )

    assert busy_response.status_code == 200

    response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Available"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["availability_status"] == "Available"


def test_update_nonexistent_delivery_partner_status(
    client,
):

    response = client.put(
        "/delivery-partners/99999/status",
        json={
            "availability_status": "Busy"
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Delivery partner not found"
    )


def test_update_delivery_partner_invalid_status(
    client,
    delivery_partner,
):

    partner_id = delivery_partner["id"]

    response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Invalid"
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Invalid availability status"
    )


def test_create_delivery_partner_invalid_name(
    client,
):

    response = client.post(
        "/delivery-partners",
        json={
            "name": "A",
            "phone": "9000000010",
            "vehicle_type": "Bike",
            "vehicle_number": "TN10AA1111",
            "current_location": "Chennai",
        },
    )

    assert response.status_code == 422


def test_create_delivery_partner_invalid_phone(
    client,
):

    response = client.post(
        "/delivery-partners",
        json={
            "name": "Test Partner",
            "phone": "123",
            "vehicle_type": "Bike",
            "vehicle_number": "TN11BB2222",
            "current_location": "Chennai",
        },
    )

    assert response.status_code == 422


def test_create_delivery_partner_invalid_vehicle_type(
    client,
):

    response = client.post(
        "/delivery-partners",
        json={
            "name": "Test Partner",
            "phone": "9000000011",
            "vehicle_type": "A",
            "vehicle_number": "TN12CC3333",
            "current_location": "Chennai",
        },
    )

    assert response.status_code == 422


def test_create_delivery_partner_invalid_vehicle_number(
    client,
):

    response = client.post(
        "/delivery-partners",
        json={
            "name": "Test Partner",
            "phone": "9000000012",
            "vehicle_type": "Bike",
            "vehicle_number": "A",
            "current_location": "Chennai",
        },
    )

    assert response.status_code == 422


def test_assign_available_driver_to_order(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order.id
    assert data["delivery_partner_id"] == partner_id
    assert data["order_status"] == "Out for Delivery"


def test_assign_driver_makes_partner_busy(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 200

    db = TestingSessionLocal()

    partner = (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.id == partner_id
        )
        .first()
    )

    db.close()

    assert partner is not None
    assert partner.availability_status == (
        DeliveryPartnerStatus.BUSY
    )


def test_assign_driver_creates_tracking_record(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 200

    db = TestingSessionLocal()

    tracking = (
        db.query(OrderTracking)
        .filter(
            OrderTracking.order_id == order.id,
            OrderTracking.status == "Out for Delivery",
        )
        .first()
    )

    db.close()

    assert tracking is not None
    assert (
        tracking.remarks
        == "Delivery partner assigned and order is out for delivery"
    )


def test_assign_driver_to_nonexistent_order(
    client,
    delivery_partner,
):

    partner_id = delivery_partner["id"]

    response = client.post(
        "/orders/99999/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Order not found"
    )


def test_assign_nonexistent_driver_to_order(
    client,
    order,
):

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": 99999
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Delivery partner not found"
    )


def test_busy_driver_cannot_be_assigned(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    status_response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Busy"
        },
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Only available delivery partners can be assigned"
    )


def test_offline_driver_cannot_be_assigned(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    status_response = client.put(
        f"/delivery-partners/{partner_id}/status",
        json={
            "availability_status": "Offline"
        },
    )

    assert status_response.status_code == 200

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Only available delivery partners can be assigned"
    )


def test_driver_cannot_be_assigned_to_delivered_order(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    db = TestingSessionLocal()

    db_order = (
        db.query(Order)
        .filter(Order.id == order.id)
        .first()
    )

    db_order.order_status = OrderStatus.DELIVERED

    db.commit()
    db.close()

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Driver cannot be assigned to this order"
    )


def test_driver_cannot_be_assigned_to_cancelled_order(
    client,
    delivery_partner,
    order,
):

    partner_id = delivery_partner["id"]

    db = TestingSessionLocal()

    db_order = (
        db.query(Order)
        .filter(Order.id == order.id)
        .first()
    )

    db_order.order_status = OrderStatus.CANCELLED

    db.commit()
    db.close()

    response = client.post(
        f"/orders/{order.id}/assign-driver",
        params={
            "partner_id": partner_id
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Driver cannot be assigned to this order"
    )


def test_assign_driver_without_partner_id(
    client,
    order,
):

    response = client.post(
        f"/orders/{order.id}/assign-driver"
    )

    assert response.status_code == 422