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
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus as PaymentModelStatus,
)
from app.models.refund import Refund


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

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(
        bind=engine
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        Base.metadata.drop_all(
            bind=engine
        )

        engine.dispose()


# ============================================================
# CLIENT FIXTURE
# ============================================================

@pytest.fixture()
def client(db):

    def override_get_db():
        yield db

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================
# USER HELPER
# ============================================================

def create_user(
    db,
    email="user@example.com",
    phone="9876543210",
):

    user = User(
        name="Test User",
        email=email,
        phone=phone,
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

@pytest.fixture()
def customer(db):

    user = create_user(
        db
    )

    customer = Customer(
        user_id=user.id,
        name="Bharath",
        email="customer@example.com",
        phone="9876543211",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# ============================================================
# ADDRESS FIXTURE
# ============================================================

@pytest.fixture()
def address(
    db,
    customer,
):

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

@pytest.fixture()
def restaurant(db):

    owner = create_user(
        db,
        email="owner@example.com",
        phone="9000000001",
    )

    restaurant = Restaurant(
        restaurant_name="Test Restaurant",
        owner_id=owner.id,
        address="100 Food Street",
        city="Chennai",
        phone="9000000002",
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


# ============================================================
# ORDER HELPER
# ============================================================

def create_order(
    db,
    customer,
    restaurant,
    address,
    total_amount=520.0,
):

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=0.0,
        total_amount=total_amount,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PAID,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


# ============================================================
# ORDER FIXTURE
# ============================================================

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


# ============================================================
# PAYMENT HELPER
# ============================================================

def create_payment(
    db,
    order,
    amount=520.0,
    transaction_id="TXN001",
):

    payment = Payment(
        order_id=order.id,
        amount=amount,
        payment_method=PaymentMethod.UPI,
        transaction_id=transaction_id,
        payment_status=PaymentModelStatus.SUCCESS,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


# ============================================================
# PAYMENT FIXTURE
# ============================================================

@pytest.fixture()
def payment(
    db,
    order,
):

    return create_payment(
        db,
        order,
    )


# ============================================================
# REFUND PAYLOAD
# ============================================================

def refund_payload(
    reason=None,
):

    if reason is None:
        return {}

    return {
        "reason": reason
    }


# ============================================================
# CREATE REFUND
# ============================================================

def test_create_refund(
    client,
    payment,
):

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Customer requested refund"
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_id"] == payment.id
    assert data["order_id"] == payment.order_id
    assert data["amount"] == 520.0
    assert data["refund_status"] == "Success"
    assert data["reason"] == (
        "Customer requested refund"
    )
    assert data["refunded_at"] is not None


# ============================================================
# CREATE REFUND WITHOUT REASON
# ============================================================

def test_create_refund_without_reason(
    client,
    payment,
):

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json={},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["amount"] == 520.0
    assert data["reason"] is None
    assert data["refund_status"] == "Success"


# ============================================================
# PAYMENT NOT FOUND
# ============================================================

def test_create_refund_payment_not_found(
    client,
):

    response = client.post(
        "/refunds/payment/9999",
        json=refund_payload(
            "Refund"
        ),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Payment not found"
    )


# ============================================================
# PAYMENT STATUS UPDATED
# ============================================================

def test_create_refund_updates_payment_status(
    client,
    db,
    payment,
):

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Refund"
        ),
    )

    assert response.status_code == 201

    db.refresh(payment)

    assert payment.payment_status == (
        PaymentModelStatus.REFUNDED
    )


# ============================================================
# ORDER STATUS UPDATED
# ============================================================

def test_create_refund_updates_order_status(
    client,
    db,
    order,
    payment,
):

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Refund"
        ),
    )

    assert response.status_code == 201

    db.refresh(order)

    assert order.payment_status == (
        PaymentStatus.REFUNDED
    )


# ============================================================
# REFUND SAVED IN DATABASE
# ============================================================

def test_create_refund_saved_in_database(
    client,
    db,
    payment,
):

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Database refund"
        ),
    )

    assert response.status_code == 201

    refund = (
        db.query(Refund)
        .filter(
            Refund.payment_id == payment.id
        )
        .first()
    )

    assert refund is not None
    assert refund.amount == 520.0
    assert refund.refund_status == "Success"
    assert refund.reason == (
        "Database refund"
    )


# ============================================================
# DUPLICATE FULL REFUND
# ============================================================

def test_duplicate_full_refund_rejected(
    client,
    payment,
):

    first = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "First refund"
        ),
    )

    assert first.status_code == 201

    second = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Second refund"
        ),
    )

    assert second.status_code == 400

    assert second.json()["detail"] == (
        "Payment has already been fully refunded"
    )


# ============================================================
# PARTIAL EXISTING REFUND
# ============================================================

def test_partial_existing_refund_refunds_remaining_amount(
    client,
    db,
    payment,
):

    existing = Refund(
        payment_id=payment.id,
        order_id=payment.order_id,
        amount=200.0,
        refund_status="Success",
        reason="Partial refund",
    )

    db.add(existing)
    db.commit()

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Remaining refund"
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["amount"] == 320.0


# ============================================================
# GET ALL REFUNDS
# ============================================================

def test_get_all_refunds(
    client,
    db,
    customer,
    restaurant,
    address,
):

    order1 = create_order(
        db,
        customer,
        restaurant,
        address,
        300.0,
    )

    order2 = create_order(
        db,
        customer,
        restaurant,
        address,
        400.0,
    )

    payment1 = create_payment(
        db,
        order1,
        300.0,
        "TXN101",
    )

    payment2 = create_payment(
        db,
        order2,
        400.0,
        "TXN102",
    )

    response1 = client.post(
        f"/refunds/payment/{payment1.id}",
        json={},
    )

    response2 = client.post(
        f"/refunds/payment/{payment2.id}",
        json={},
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    response = client.get(
        "/refunds"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert {
        item["payment_id"]
        for item in data
    } == {
        payment1.id,
        payment2.id,
    }


# ============================================================
# GET REFUND
# ============================================================

def test_get_refund(
    client,
    payment,
):

    create_response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "Get refund"
        ),
    )

    assert create_response.status_code == 201

    refund_id = create_response.json()["id"]

    response = client.get(
        f"/refunds/{refund_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == refund_id
    assert data["payment_id"] == payment.id
    assert data["amount"] == 520.0
    assert data["reason"] == "Get refund"


# ============================================================
# REFUND NOT FOUND
# ============================================================

def test_get_refund_not_found(
    client,
):

    response = client.get(
        "/refunds/9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Refund not found"
    )


# ============================================================
# REASON TOO LONG
# ============================================================

def test_refund_reason_too_long(
    client,
    payment,
):

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            "x" * 501
        ),
    )

    assert response.status_code == 422


# ============================================================
# REASON MAXIMUM LENGTH
# ============================================================

def test_refund_reason_at_max_length(
    client,
    payment,
):

    reason = "x" * 500

    response = client.post(
        f"/refunds/payment/{payment.id}",
        json=refund_payload(
            reason
        ),
    )

    assert response.status_code == 201

    assert response.json()["reason"] == reason