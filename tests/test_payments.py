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


# ============================================================
# CUSTOMER FIXTURE
# ============================================================

@pytest.fixture()
def customer(
    db,
):

    user = create_user(
        db,
        name="Customer User",
        email="customeruser@example.com",
        phone="9876543210",
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
# RESTAURANT OWNER
# ============================================================

@pytest.fixture()
def owner(
    db,
):

    return create_user(
        db,
        name="Restaurant Owner",
        email="owner@example.com",
        phone="9000000001",
        role="Restaurant Owner",
    )


# ============================================================
# RESTAURANT FIXTURE
# ============================================================

@pytest.fixture()
def restaurant(
    db,
    owner,
):

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
    status=OrderStatus.PENDING,
    payment_status=PaymentStatus.PENDING,
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
        order_status=status,
        payment_status=payment_status,
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
# PAYMENT PAYLOAD HELPER
# ============================================================

def payment_payload(
    amount=520.0,
    payment_method="UPI",
    transaction_id="TXN001",
):

    return {
        "amount": amount,
        "payment_method": payment_method,
        "transaction_id": transaction_id,
    }


# ============================================================
# CREATE PAYMENT - UPI
# ============================================================

def test_create_payment_upi(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="UPI",
            transaction_id="TXN001",
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order.id
    assert data["amount"] == 520.0
    assert data["payment_method"] == "UPI"
    assert data["transaction_id"] == "TXN001"
    assert data["payment_status"] == "Success"
    assert data["paid_at"] is not None


# ============================================================
# CREATE PAYMENT - CARD
# ============================================================

def test_create_payment_card(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="Card",
            transaction_id="TXN002",
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_method"] == "Card"
    assert data["payment_status"] == "Success"


# ============================================================
# CREATE PAYMENT - WALLET
# ============================================================

def test_create_payment_wallet(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="Wallet",
            transaction_id="TXN003",
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_method"] == "Wallet"
    assert data["payment_status"] == "Success"


# ============================================================
# CREATE PAYMENT - CASH ON DELIVERY
# ============================================================

def test_create_payment_cash_on_delivery(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="Cash on Delivery",
            transaction_id="TXN004",
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_method"] == "Cash on Delivery"
    assert data["payment_status"] == "Success"


# ============================================================
# ORDER PAYMENT STATUS UPDATED
# ============================================================

def test_create_payment_updates_order_status(
    client,
    db,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN005",
        ),
    )

    assert response.status_code == 201

    db.refresh(order)

    assert order.payment_status == PaymentStatus.PAID


# ============================================================
# PAYMENT AMOUNT MISMATCH
# ============================================================

def test_payment_amount_mismatch(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            amount=500.0,
            transaction_id="TXN006",
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment amount must match order total"
    )


# ============================================================
# PAYMENT AMOUNT TOO HIGH
# ============================================================

def test_payment_amount_too_high(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            amount=600.0,
            transaction_id="TXN007",
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment amount must match order total"
    )


# ============================================================
# PAYMENT AMOUNT ZERO
# ============================================================

def test_payment_amount_zero(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            amount=0,
            transaction_id="TXN008",
        ),
    )

    assert response.status_code == 422


# ============================================================
# PAYMENT AMOUNT NEGATIVE
# ============================================================

def test_payment_amount_negative(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            amount=-100,
            transaction_id="TXN009",
        ),
    )

    assert response.status_code == 422


# ============================================================
# INVALID PAYMENT METHOD
# ============================================================

def test_invalid_payment_method(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="Bitcoin",
            transaction_id="TXN010",
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid payment method. "
        "Allowed methods: UPI, Card, Wallet, "
        "Cash on Delivery"
    )


# ============================================================
# EMPTY PAYMENT METHOD
# ============================================================

def test_empty_payment_method(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="",
            transaction_id="TXN011",
        ),
    )

    assert response.status_code == 422


# ============================================================
# PAYMENT METHOD TOO LONG
# ============================================================

def test_payment_method_too_long(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            payment_method="X" * 31,
            transaction_id="TXN012",
        ),
    )

    assert response.status_code == 422


# ============================================================
# ORDER NOT FOUND
# ============================================================

def test_create_payment_order_not_found(
    client,
):

    response = client.post(
        "/payments/9999",
        json=payment_payload(
            transaction_id="TXN013",
        ),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


# ============================================================
# CANCELLED ORDER CANNOT BE PAID
# ============================================================

def test_cancelled_order_cannot_be_paid(
    client,
    db,
    customer,
    restaurant,
    address,
):

    cancelled_order = create_order(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.CANCELLED,
    )

    response = client.post(
        f"/payments/{cancelled_order.id}",
        json=payment_payload(
            transaction_id="TXN014",
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Cancelled orders cannot be paid"
    )


# ============================================================
# DUPLICATE PAYMENT FOR SAME ORDER
# ============================================================

def test_duplicate_payment_for_same_order(
    client,
    order,
):

    first_response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN015",
        ),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN016",
        ),
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Payment already exists for this order"
    )


# ============================================================
# DUPLICATE TRANSACTION ID
# ============================================================

def test_duplicate_transaction_id(
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
        total_amount=520.0,
    )

    order2 = create_order(
        db,
        customer,
        restaurant,
        address,
        total_amount=520.0,
    )

    first_response = client.post(
        f"/payments/{order1.id}",
        json=payment_payload(
            transaction_id="DUPLICATE-TXN",
        ),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/payments/{order2.id}",
        json=payment_payload(
            transaction_id="DUPLICATE-TXN",
        ),
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Transaction ID already exists"
    )


# ============================================================
# TRANSACTION ID IS TRIMMED
# ============================================================

def test_transaction_id_is_trimmed(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="   TXN017   ",
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["transaction_id"] == "TXN017"


# ============================================================
# TRANSACTION ID EMPTY AFTER TRIM
# ============================================================

def test_transaction_id_empty_after_trim(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="   ",
        ),
    )

    # Pydantic accepts this because it meets the length
    # requirement; repository then rejects it.
    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Transaction ID cannot be empty"
    )


# ============================================================
# TRANSACTION ID TOO SHORT
# ============================================================

def test_transaction_id_too_short(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="AB",
        ),
    )

    assert response.status_code == 422


# ============================================================
# TRANSACTION ID TOO LONG
# ============================================================

def test_transaction_id_too_long(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="X" * 101,
        ),
    )

    assert response.status_code == 422


# ============================================================
# GET PAYMENT BY ID
# ============================================================

def test_get_payment_by_id(
    client,
    order,
):

    create_response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN018",
        ),
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/payments/{payment_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["order_id"] == order.id
    assert data["amount"] == 520.0
    assert data["payment_method"] == "UPI"
    assert data["transaction_id"] == "TXN018"
    assert data["payment_status"] == "Success"


# ============================================================
# GET PAYMENT NOT FOUND
# ============================================================

def test_get_payment_not_found(
    client,
):

    response = client.get(
        "/payments/9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Payment not found"
    )


# ============================================================
# GET ORDER PAYMENT
# ============================================================

def test_get_order_payment(
    client,
    order,
):

    create_response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN019",
        ),
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/payments/order/{order.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_id"] == order.id
    assert data["amount"] == 520.0
    assert data["payment_method"] == "UPI"
    assert data["transaction_id"] == "TXN019"
    assert data["payment_status"] == "Success"


# ============================================================
# GET ORDER PAYMENT - ORDER NOT FOUND
# ============================================================

def test_get_order_payment_order_not_found(
    client,
):

    response = client.get(
        "/payments/order/9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


# ============================================================
# GET ORDER PAYMENT - PAYMENT NOT FOUND
# ============================================================

def test_get_order_payment_not_found(
    client,
    order,
):

    response = client.get(
        f"/payments/order/{order.id}"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Payment not found for this order"
    )


# ============================================================
# PAYMENT STORED IN DATABASE
# ============================================================

def test_payment_saved_in_database(
    client,
    db,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN020",
        ),
    )

    assert response.status_code == 201

    payment = (
        db.query(Payment)
        .filter(
            Payment.order_id == order.id
        )
        .first()
    )

    assert payment is not None
    assert payment.amount == 520.0
    assert payment.payment_method == PaymentMethod.UPI
    assert payment.transaction_id == "TXN020"
    assert payment.payment_status == (
        PaymentModelStatus.SUCCESS
    )
    assert payment.paid_at is not None


# ============================================================
# PAYMENT RESPONSE STATUS
# ============================================================

def test_payment_status_is_success(
    client,
    order,
):

    response = client.post(
        f"/payments/{order.id}",
        json=payment_payload(
            transaction_id="TXN021",
        ),
    )

    assert response.status_code == 201

    assert response.json()["payment_status"] == (
        "Success"
    )


# ============================================================
# PAYMENT AMOUNT WITH TWO DECIMAL PLACES
# ============================================================

def test_payment_amount_two_decimal_places(
    client,
    db,
    customer,
    restaurant,
    address,
):

    special_order = create_order(
        db,
        customer,
        restaurant,
        address,
        total_amount=520.55,
    )

    response = client.post(
        f"/payments/{special_order.id}",
        json={
            "amount": 520.55,
            "payment_method": "UPI",
            "transaction_id": "TXN022",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["amount"] == 520.55
    assert data["payment_status"] == "Success"