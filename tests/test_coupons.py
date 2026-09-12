from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.customer import Customer


# ============================================================
# TEST DATABASE
# ============================================================

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
# USER FIXTURE
# ============================================================

@pytest.fixture
def user():
    db = TestingSessionLocal()

    user = User(
        name="Coupon Test User",
        email="couponuser@gmail.com",
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


# ============================================================
# CUSTOMER FIXTURE
# ============================================================

@pytest.fixture
def customer(user):
    db = TestingSessionLocal()

    customer = Customer(
        user_id=user.id,
        name="Coupon Customer",
        email="couponcustomer@gmail.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    db.close()

    return customer


# ============================================================
# ACTIVE COUPON PAYLOAD
# ============================================================

@pytest.fixture
def active_coupon_payload():
    now = datetime.now(timezone.utc)

    return {
        "coupon_code": "SAVE10",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }


# ============================================================
# TEST 1
# CREATE COUPON
# ============================================================

def test_create_coupon(
    client,
    active_coupon_payload,
):

    response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["coupon_code"] == "SAVE10"
    assert data["discount_type"] == "Percentage"
    assert data["discount_value"] == 10
    assert data["minimum_order_value"] == 100
    assert data["maximum_discount"] == 50
    assert data["usage_limit"] == 10
    assert data["status"] == "Active"


# ============================================================
# TEST 2
# GET COUPONS
# ============================================================

def test_get_coupons(
    client,
    active_coupon_payload,
):

    create_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert create_response.status_code == 201

    response = client.get("/coupons")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["coupon_code"] == "SAVE10"


# ============================================================
# TEST 3
# CREATE FIXED COUPON
# ============================================================

def test_create_fixed_coupon(client):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "FIXED50",
        "discount_type": "Fixed",
        "discount_value": 50,
        "minimum_order_value": 200,
        "maximum_discount": None,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 5,
        "status": "Active",
    }

    response = client.post(
        "/coupons",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["coupon_code"] == "FIXED50"
    assert data["discount_type"] == "Fixed"
    assert data["discount_value"] == 50


# ============================================================
# TEST 4
# DUPLICATE COUPON CODE
# ============================================================

def test_duplicate_coupon_code(
    client,
    active_coupon_payload,
):

    first_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Coupon code already exists"
    )


# ============================================================
# TEST 5
# INVALID DISCOUNT TYPE
# ============================================================

def test_invalid_discount_type(client):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "INVALIDTYPE",
        "discount_type": "Invalid",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }

    response = client.post(
        "/coupons",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Discount type must be Percentage or Fixed"
    )


# ============================================================
# TEST 6
# EXPIRY BEFORE START DATE
# ============================================================

def test_expiry_before_start_date(client):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "BADDATE",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now + timedelta(days=5)).isoformat(),
        "expiry_date": (now + timedelta(days=2)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }

    response = client.post(
        "/coupons",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Expiry date must be after start date"
    )


# ============================================================
# TEST 7
# APPLY PERCENTAGE COUPON
# ============================================================

def test_apply_percentage_coupon(
    client,
    customer,
    active_coupon_payload,
):

    create_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["coupon_code"] == "SAVE10"
    assert data["order_value"] == 500
    assert data["discount_amount"] == 50
    assert data["final_amount"] == 450


# ============================================================
# TEST 8
# APPLY FIXED COUPON
# ============================================================

def test_apply_fixed_coupon(
    client,
    customer,
):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "FIXED50",
        "discount_type": "Fixed",
        "discount_value": 50,
        "minimum_order_value": 100,
        "maximum_discount": None,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }

    create_response = client.post(
        "/coupons",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "FIXED50",
            "customer_id": customer.id,
            "order_value": 300,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["coupon_code"] == "FIXED50"
    assert data["order_value"] == 300
    assert data["discount_amount"] == 50
    assert data["final_amount"] == 250


# ============================================================
# TEST 9
# MAXIMUM DISCOUNT
# ============================================================

def test_percentage_coupon_maximum_discount(
    client,
    customer,
):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "MAXDISCOUNT",
        "discount_type": "Percentage",
        "discount_value": 20,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }

    create_response = client.post(
        "/coupons",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "MAXDISCOUNT",
            "customer_id": customer.id,
            "order_value": 1000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["discount_amount"] == 50
    assert data["final_amount"] == 950


# ============================================================
# TEST 10
# NON-EXISTENT COUPON
# ============================================================

def test_apply_nonexistent_coupon(
    client,
    customer,
):

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "NOTFOUND",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Coupon not found"
    )


# ============================================================
# TEST 11
# COUPON NOT ACTIVE YET
# ============================================================

def test_coupon_not_active_yet(
    client,
    customer,
):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "FUTURE10",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now + timedelta(days=2)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }

    create_response = client.post(
        "/coupons",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "FUTURE10",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Coupon is not active yet"
    )


# ============================================================
# TEST 12
# EXPIRED COUPON
# ============================================================

def test_expired_coupon(
    client,
    customer,
):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "EXPIRED10",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=7)).isoformat(),
        "expiry_date": (now - timedelta(days=1)).isoformat(),
        "usage_limit": 10,
        "status": "Active",
    }

    create_response = client.post(
        "/coupons",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "EXPIRED10",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Coupon has expired"
    )


# ============================================================
# TEST 13
# INACTIVE COUPON
# ============================================================

def test_inactive_coupon(
    client,
    customer,
):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "INACTIVE10",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "status": "Inactive",
    }

    create_response = client.post(
        "/coupons",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "INACTIVE10",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Coupon is inactive"
    )


# ============================================================
# TEST 14
# MINIMUM ORDER VALUE
# ============================================================

def test_minimum_order_value_not_reached(
    client,
    customer,
    active_coupon_payload,
):

    create_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "customer_id": customer.id,
            "order_value": 50,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Minimum order value is 100.0"
    )


# ============================================================
# TEST 15
# COUPON CANNOT BE USED TWICE
# ============================================================

def test_coupon_cannot_be_used_twice_by_same_customer(
    client,
    customer,
    active_coupon_payload,
):

    create_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert create_response.status_code == 201

    first_response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Coupon already used by this customer"
    )


# ============================================================
# TEST 16
# COUPON USAGE LIMIT
# ============================================================

def test_coupon_usage_limit_exceeded(
    client,
    customer,
    user,
):

    db = TestingSessionLocal()

    second_user = User(
        name="Second Coupon User",
        email="secondcouponuser@gmail.com",
        phone="9876543211",
        password_hash="hashed_password",
        role="Customer",
        is_active=True,
        is_deleted=False,
    )

    db.add(second_user)
    db.commit()
    db.refresh(second_user)

    second_customer = Customer(
        user_id=second_user.id,
        name="Second Coupon Customer",
        email="secondcouponcustomer@gmail.com",
        phone="9876543211",
    )

    db.add(second_customer)
    db.commit()
    db.refresh(second_customer)

    db.close()

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "LIMITONE",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 1,
        "status": "Active",
    }

    create_response = client.post(
        "/coupons",
        json=payload,
    )

    assert create_response.status_code == 201

    first_response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "LIMITONE",
            "customer_id": customer.id,
            "order_value": 500,
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "LIMITONE",
            "customer_id": second_customer.id,
            "order_value": 500,
        },
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Coupon usage limit exceeded"
    )


# ============================================================
# TEST 17
# INVALID CUSTOMER ID
# ============================================================

def test_apply_coupon_with_invalid_customer_id(
    client,
    active_coupon_payload,
):

    create_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "customer_id": 99999,
            "order_value": 500,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Customer not found"


# ============================================================
# TEST 18
# INVALID ORDER VALUE
# ============================================================

def test_coupon_invalid_order_value(
    client,
    customer,
    active_coupon_payload,
):

    create_response = client.post(
        "/coupons",
        json=active_coupon_payload,
    )

    assert create_response.status_code == 201

    response = client.post(
        "/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "customer_id": customer.id,
            "order_value": 0,
        },
    )

    assert response.status_code == 422


# ============================================================
# TEST 19
# INVALID USAGE LIMIT
# ============================================================

def test_coupon_invalid_usage_limit(client):

    now = datetime.now(timezone.utc)

    payload = {
        "coupon_code": "BADLIMIT",
        "discount_type": "Percentage",
        "discount_value": 10,
        "minimum_order_value": 100,
        "maximum_discount": 50,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=7)).isoformat(),
        "usage_limit": 0,
        "status": "Active",
    }

    response = client.post(
        "/coupons",
        json=payload,
    )

    assert response.status_code == 422