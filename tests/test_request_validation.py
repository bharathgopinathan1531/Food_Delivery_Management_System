from pydantic import ValidationError
import pytest

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
)

from app.schemas.customer import (
    CustomerCreate,
    AddressCreate,
)


# ============================================================
# AUTH REQUEST VALIDATION
# ============================================================

def test_register_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Bharath",
            email="invalid-email",
            password="password123",
        )


def test_register_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Bharath",
            email="bharath_validation@example.com",
            password="short",
        )


def test_register_short_name():
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="B",
            email="bharath_validation2@example.com",
            password="password123",
        )


def test_login_invalid_email():
    with pytest.raises(ValidationError):
        LoginRequest(
            email="invalid-email",
            password="password123",
        )


def test_change_password_short_new_password():
    with pytest.raises(ValidationError):
        ChangePasswordRequest(
            current_password="oldpassword123",
            new_password="short",
        )


# ============================================================
# CUSTOMER REQUEST VALIDATION
# ============================================================

def test_customer_invalid_email():
    with pytest.raises(ValidationError):
        CustomerCreate(
            name="Bharath",
            email="invalid-email",
            phone="9876543210",
        )


def test_customer_short_name():
    with pytest.raises(ValidationError):
        CustomerCreate(
            name="B",
            email="customer_validation@example.com",
            phone="9876543210",
        )


def test_customer_invalid_phone_length():
    with pytest.raises(ValidationError):
        CustomerCreate(
            name="Bharath",
            email="customer_validation2@example.com",
            phone="123",
        )


# ============================================================
# ADDRESS REQUEST VALIDATION
# ============================================================

def test_address_short_address_line():
    with pytest.raises(ValidationError):
        AddressCreate(
            address_line="ABC",
            city="Chennai",
            pincode="600001",
        )


def test_address_short_city():
    with pytest.raises(ValidationError):
        AddressCreate(
            address_line="123 Main Street",
            city="C",
            pincode="600001",
        )


def test_address_short_pincode():
    with pytest.raises(ValidationError):
        AddressCreate(
            address_line="123 Main Street",
            city="Chennai",
            pincode="123",
        )


# ============================================================
# VALID REQUEST
# ============================================================

def test_valid_register_request():
    request = RegisterRequest(
        name="Bharath",
        email="bharath_valid@example.com",
        password="password123",
    )

    assert request.name == "Bharath"
    assert request.email == "bharath_valid@example.com"
    assert request.password == "password123"


def test_valid_customer_request():
    request = CustomerCreate(
        name="Bharath",
        email="customer_valid@example.com",
        phone="9876543210",
    )

    assert request.name == "Bharath"
    assert request.email == "customer_valid@example.com"
    assert request.phone == "9876543210"
    
# ============================================================
# FASTAPI 422 REQUEST VALIDATION
# ============================================================

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_missing_required_fields_returns_422():
    response = client.post(
        "/auth/register",
        json={}
    )

    assert response.status_code == 422


def test_register_invalid_email_returns_422():
    response = client.post(
        "/auth/register",
        json={
            "name": "Bharath",
            "email": "invalid-email",
            "password": "password123",
            "role": "Customer",
        }
    )

    assert response.status_code == 422


def test_register_short_password_returns_422():
    response = client.post(
        "/auth/register",
        json={
            "name": "Bharath",
            "email": "bharath_422@example.com",
            "password": "short",
            "role": "Customer",
        }
    )

    assert response.status_code == 422    