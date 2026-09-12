from datetime import time
from unittest.mock import patch

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

from app.services.notification_service import (
    send_notification,
    notify_order_placed,
    notify_order_accepted,
    notify_food_ready,
    notify_driver_assigned,
    notify_out_for_delivery,
    notify_order_delivered,
    notify_payment_success,
    notify_refund_processed,
)


# ============================================================
# TEST DATABASE
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# DATABASE OVERRIDE
# ============================================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ============================================================
# CLIENT FIXTURE
# ============================================================

@pytest.fixture
def client():

    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture
def db():

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================
# USER FIXTURE
# ============================================================

@pytest.fixture
def user(db):

    user = User(
        name="Test User",
        email="testuser@gmail.com",
        phone="9876543210",
        password_hash="hashed-password",
        role="Customer",
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# CUSTOMER FIXTURE
# ============================================================

@pytest.fixture
def customer(db, user):

    customer = Customer(
        user_id=user.id,
        name="Bharath",
        email="customer@gmail.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# ============================================================
# ADDRESS FIXTURE
# ============================================================

@pytest.fixture
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


# ============================================================
# RESTAURANT FIXTURE
# ============================================================

@pytest.fixture
def restaurant(db, user):

    restaurant = Restaurant(
        restaurant_name="Test Restaurant",
        owner_id=user.id,
        address="123 Main Street",
        city="Chennai",
        phone="9000000001",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


# ============================================================
# MENU ITEM FIXTURE
# ============================================================

@pytest.fixture
def menu_item(db, restaurant):

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Chicken biryani",
        price=250.0,
        preparation_time=25,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# ============================================================
# TEST 1
# SEND NOTIFICATION
# ============================================================

def test_send_notification():

    result = send_notification(
        notification_type="Test Notification",
        recipient_id=1,
        message="Test notification message",
    )

    assert result["notification_type"] == (
        "Test Notification"
    )

    assert result["recipient_id"] == 1

    assert result["message"] == (
        "Test notification message"
    )

    assert "created_at" in result


# ============================================================
# TEST 2
# ORDER PLACED
# ============================================================

def test_order_placed_notification():

    result = notify_order_placed(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Order Placed"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 3
# ORDER ACCEPTED
# ============================================================

def test_order_accepted_notification():

    result = notify_order_accepted(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Order Accepted"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 4
# FOOD READY
# ============================================================

def test_food_ready_notification():

    result = notify_food_ready(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Food Ready"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 5
# DRIVER ASSIGNED
# ============================================================

def test_driver_assigned_notification():

    result = notify_driver_assigned(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Driver Assigned"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 6
# OUT FOR DELIVERY
# ============================================================

def test_out_for_delivery_notification():

    result = notify_out_for_delivery(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Out for Delivery"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 7
# ORDER DELIVERED
# ============================================================

def test_order_delivered_notification():

    result = notify_order_delivered(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Order Delivered"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 8
# PAYMENT SUCCESS
# ============================================================

def test_payment_success_notification():

    result = notify_payment_success(
        recipient_id=1,
        order_id=101,
    )

    assert result["notification_type"] == (
        "Payment Success"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]


# ============================================================
# TEST 9
# REFUND PROCESSED
# ============================================================

def test_refund_processed_notification():

    result = notify_refund_processed(
        recipient_id=1,
        order_id=101,
        amount=500.00,
    )

    assert result["notification_type"] == (
        "Refund Processed"
    )

    assert result["recipient_id"] == 1

    assert "101" in result["message"]

    assert "500.00" in result["message"]


# ============================================================
# TEST 10
# ORDER PLACED USES BACKGROUND TASK
# ============================================================

def test_order_placed_uses_background_task(
    client,
    customer,
    restaurant,
    menu_item,
    address,
):

    with patch(
        "app.routes.orders.notify_order_placed"
    ) as mock_notification:

        response = client.post(
            "/orders",
            json={
                "customer_id": customer.id,
                "restaurant_id": restaurant.id,
                "address_id": address.id,
                "items": [
                    {
                        "menu_item_id": menu_item.id,
                        "quantity": 1,
                    }
                ],
                "delivery_fee": 20,
                "discount": 0,
                "tax": 10,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer.id

    mock_notification.assert_called_once_with(
        customer.id,
        data["id"],
    )


# ============================================================
# TEST 11
# ORDER ACCEPTED USES BACKGROUND TASK
# ============================================================

def test_order_accepted_uses_background_task(
    client,
    customer,
    restaurant,
    menu_item,
    address,
):

    create_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
            "delivery_fee": 20,
            "discount": 0,
            "tax": 10,
        },
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    with patch(
        "app.routes.orders.notify_order_accepted"
    ) as mock_notification:

        response = client.post(
            f"/orders/{order_id}/accept"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["customer_id"] == customer.id
    assert data["order_status"] == "Accepted"

    mock_notification.assert_called_once_with(
        customer.id,
        order_id,
    )


# ============================================================
# TEST 12
# FOOD READY USES BACKGROUND TASK
# ============================================================

def test_food_ready_uses_background_task(
    client,
    customer,
    restaurant,
    menu_item,
    address,
):

    create_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
            "delivery_fee": 20,
            "discount": 0,
            "tax": 10,
        },
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    accept_response = client.post(
        f"/orders/{order_id}/accept"
    )

    assert accept_response.status_code == 200
    assert accept_response.json()["order_status"] == "Accepted"

    with patch(
        "app.routes.orders.notify_food_ready"
    ) as mock_notification:

        response = client.post(
            f"/orders/{order_id}/food-ready"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["customer_id"] == customer.id
    assert data["order_status"] == "Ready"

    mock_notification.assert_called_once_with(
        customer.id,
        order_id,
    )


# ============================================================
# TEST 13
# DRIVER ASSIGNED USES BACKGROUND TASK
# ============================================================

def test_driver_assigned_uses_background_task(
    client,
    customer,
    restaurant,
    menu_item,
    address,
):

    from app.models.delivery_partner import (
        DeliveryPartner,
        DeliveryPartnerStatus,
    )

    db_session = TestingSessionLocal()

    try:
        partner = DeliveryPartner(
            name="Test Driver",
            phone="9999999999",
            vehicle_type="Bike",
            vehicle_number="TN01AB1234",
            availability_status=DeliveryPartnerStatus.AVAILABLE,
            current_location="Chennai",
        )

        db_session.add(partner)
        db_session.commit()
        db_session.refresh(partner)

        partner_id = partner.id

    finally:
        db_session.close()

    create_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
            "delivery_fee": 20,
            "discount": 0,
            "tax": 10,
        },
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    with patch(
        "app.routes.orders.notify_driver_assigned"
    ) as mock_notification:

        response = client.post(
            f"/orders/{order_id}/assign-driver",
            params={
                "partner_id": partner_id
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["customer_id"] == customer.id
    assert data["delivery_partner_id"] == partner_id
    assert data["order_status"] == "Out for Delivery"

    mock_notification.assert_called_once_with(
        customer.id,
        order_id,
    )


# ============================================================
# TEST 14
# OUT FOR DELIVERY USES BACKGROUND TASK
# ============================================================

def test_out_for_delivery_uses_background_task(
    client,
    db,
    customer,
    restaurant,
    menu_item,
    address,
):

    from app.models.delivery_partner import DeliveryPartner

    partner = DeliveryPartner(
        name="Delivery Partner",
        phone="9876543210",
        vehicle_type="Bike",
        vehicle_number="TN01AB1234",
        current_location="Chennai",
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    order_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "delivery_fee": 40,
            "discount": 0,
            "tax": 10,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    with patch(
        "app.routes.orders.notify_out_for_delivery"
    ) as mock_notification:

        response = client.post(
            f"/orders/{order_id}/assign-driver",
            params={
                "partner_id": partner.id,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["delivery_partner_id"] == partner.id
    assert data["order_status"] == "Out for Delivery"

    mock_notification.assert_called_once_with(
        customer.id,
        order_id,
    )


# ============================================================
# TEST 15
# ORDER DELIVERED USES BACKGROUND TASK
# ============================================================

def test_order_delivered_uses_background_task(
    client,
    db,
    customer,
    restaurant,
    menu_item,
    address,
):

    from app.models.delivery_partner import DeliveryPartner

    partner = DeliveryPartner(
        name="Delivery Partner",
        phone="9876543211",
        vehicle_type="Bike",
        vehicle_number="TN01AB1235",
        current_location="Chennai",
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    order_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "delivery_fee": 40,
            "discount": 0,
            "tax": 10,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    assign_response = client.post(
        f"/orders/{order_id}/assign-driver",
        params={
            "partner_id": partner.id,
        },
    )

    assert assign_response.status_code == 200

    assign_data = assign_response.json()

    assert assign_data["id"] == order_id
    assert assign_data["delivery_partner_id"] == partner.id
    assert assign_data["order_status"] == "Out for Delivery"

    with patch(
        "app.routes.orders.notify_order_delivered"
    ) as mock_notification:

        response = client.post(
            f"/orders/{order_id}/deliver"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order_id
    assert data["order_status"] == "Delivered"

    mock_notification.assert_called_once_with(
        customer.id,
        order_id,
    )


# ============================================================
# TEST 16
# PAYMENT SUCCESS USES BACKGROUND TASK
# ============================================================

def test_payment_success_uses_background_task(
    client,
    db,
    customer,
    restaurant,
    menu_item,
    address,
):

    from unittest.mock import patch

    order_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "delivery_fee": 40,
            "discount": 0,
            "tax": 10,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert order_response.status_code == 201

    order_data = order_response.json()

    order_id = order_data["id"]
    order_total = order_data["total_amount"]

    with patch(
        "app.routes.payments.notify_payment_success"
    ) as mock_notification:

        response = client.post(
            f"/payments/{order_id}",
            json={
                "amount": order_total,
                "payment_method": "UPI",
                "transaction_id": "TXN-PAYMENT-SUCCESS-001",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order_id
    assert data["amount"] == order_total

    mock_notification.assert_called_once_with(
        order_id,
        data["id"],
    )


# ============================================================
# TEST 17
# REFUND PROCESSED USES BACKGROUND TASK
# ============================================================

def test_refund_processed_uses_background_task(
    client,
    db,
    customer,
    restaurant,
    menu_item,
    address,
):

    from app.models.payment import (
        Payment,
        PaymentMethod,
        PaymentStatus,
    )

    order_response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "restaurant_id": restaurant.id,
            "address_id": address.id,
            "delivery_fee": 40,
            "discount": 0,
            "tax": 10,
            "items": [
                {
                    "menu_item_id": menu_item.id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert order_response.status_code == 201

    order_data = order_response.json()

    order_id = order_data["id"]
    order_total = order_data["total_amount"]

    payment = Payment(
        order_id=order_id,
        amount=order_total,
        payment_method=PaymentMethod.UPI,
        transaction_id="TXN-REFUND-TEST-001",
        payment_status=PaymentStatus.SUCCESS,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    with patch(
        "app.routes.refunds.notify_refund_processed"
    ) as mock_notification:

        response = client.post(
            f"/refunds/payment/{payment.id}",
            json={
                "amount": 100.00,
                "reason": "Customer requested refund",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_id"] == payment.id
    assert data["order_id"] == order_id

    # The existing refund logic processes the full
    # payment/order amount.
    assert data["amount"] == 300.00

    mock_notification.assert_called_once_with(
        customer.id,
        order_id,
        300.00,
    )