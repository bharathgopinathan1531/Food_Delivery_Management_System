import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


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


def customer_payload(
    name="Test Customer",
    email="customer@gmail.com",
    phone="9876543210",
):
    return {
        "name": name,
        "email": email,
        "phone": phone,
    }


def address_payload(
    address_line="123 Main Street",
    city="Chennai",
    pincode="600001",
    latitude=13.0827,
    longitude=80.2707,
    address_type="Home",
    is_default=False,
):
    return {
        "address_line": address_line,
        "city": city,
        "pincode": pincode,
        "latitude": latitude,
        "longitude": longitude,
        "address_type": address_type,
        "is_default": is_default,
    }


def test_create_customer(client):

    response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["name"] == "Test Customer"
    assert data["email"] == "customer@gmail.com"
    assert data["phone"] == "9876543210"


def test_create_customer_with_different_data(client):

    response = client.post(
        "/customers",
        json=customer_payload(
            name="Bharath",
            email="bharath_customer@gmail.com",
            phone="9123456789",
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Bharath"
    assert data["email"] == "bharath_customer@gmail.com"
    assert data["phone"] == "9123456789"


def test_create_duplicate_customer_email(client):

    first_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/customers",
        json=customer_payload(
            name="Another Customer",
            email="customer@gmail.com",
            phone="9999999999",
        ),
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Customer with this email already exists"
    )


def test_get_customer(client):

    create_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.get(
        f"/customers/{customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["name"] == "Test Customer"
    assert data["email"] == "customer@gmail.com"
    assert data["phone"] == "9876543210"


def test_get_nonexistent_customer(client):

    response = client.get(
        "/customers/99999"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Customer not found"
    )


def test_create_customer_name_too_short(client):

    response = client.post(
        "/customers",
        json={
            "name": "A",
            "email": "shortname@gmail.com",
            "phone": "9876543210",
        },
    )

    assert response.status_code == 422


def test_create_customer_invalid_email(client):

    response = client.post(
        "/customers",
        json={
            "name": "Test Customer",
            "email": "invalid-email",
            "phone": "9876543210",
        },
    )

    assert response.status_code == 422


def test_create_customer_phone_too_short(client):

    response = client.post(
        "/customers",
        json={
            "name": "Test Customer",
            "email": "shortphone@gmail.com",
            "phone": "12345",
        },
    )

    assert response.status_code == 422


def test_create_customer_missing_required_field(client):

    response = client.post(
        "/customers",
        json={
            "name": "Test Customer",
            "email": "missingphone@gmail.com",
        },
    )

    assert response.status_code == 422


def test_create_customer_address(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    response = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            is_default=True
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["customer_id"] == customer_id
    assert data["address_line"] == "123 Main Street"
    assert data["city"] == "Chennai"
    assert data["pincode"] == "600001"
    assert data["latitude"] == 13.0827
    assert data["longitude"] == 80.2707
    assert data["address_type"] == "Home"
    assert data["is_default"] is True


def test_create_address_for_nonexistent_customer(client):

    response = client.post(
        "/customers/99999/addresses",
        json=address_payload(),
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Customer not found"
    )


def test_get_customer_addresses(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    first_address = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            address_line="123 Main Street",
            city="Chennai",
            pincode="600001",
            address_type="Home",
            is_default=True,
        ),
    )

    assert first_address.status_code == 201

    second_address = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            address_line="456 Anna Nagar",
            city="Chennai",
            pincode="600040",
            address_type="Work",
            is_default=False,
        ),
    )

    assert second_address.status_code == 201

    response = client.get(
        f"/customers/{customer_id}/addresses"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    assert data[0]["customer_id"] == customer_id
    assert data[1]["customer_id"] == customer_id


def test_get_addresses_for_nonexistent_customer(client):

    response = client.get(
        "/customers/99999/addresses"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Customer not found"
    )


def test_default_address_replaces_previous_default(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    first_response = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            address_line="First Address",
            city="Chennai",
            pincode="600001",
            is_default=True,
        ),
    )

    assert first_response.status_code == 201

    first_address_id = first_response.json()["id"]

    second_response = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            address_line="Second Address",
            city="Chennai",
            pincode="600002",
            is_default=True,
        ),
    )

    assert second_response.status_code == 201

    second_address_id = second_response.json()["id"]

    response = client.get(
        f"/customers/{customer_id}/addresses"
    )

    assert response.status_code == 200

    addresses = response.json()

    first_address = next(
        item
        for item in addresses
        if item["id"] == first_address_id
    )

    second_address = next(
        item
        for item in addresses
        if item["id"] == second_address_id
    )

    assert first_address["is_default"] is False
    assert second_address["is_default"] is True


def test_update_customer_address(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    address_response = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(),
    )

    assert address_response.status_code == 201

    address_id = address_response.json()["id"]

    response = client.put(
        f"/addresses/{address_id}",
        json={
            "address_line": "789 Updated Street",
            "city": "Bangalore",
            "pincode": "560001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == address_id
    assert data["customer_id"] == customer_id
    assert data["address_line"] == "789 Updated Street"
    assert data["city"] == "Bangalore"
    assert data["pincode"] == "560001"


def test_update_address_to_default(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    first_response = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            address_line="First Address",
            city="Chennai",
            pincode="600001",
            is_default=True,
        ),
    )

    assert first_response.status_code == 201

    first_address_id = first_response.json()["id"]

    second_response = client.post(
        f"/customers/{customer_id}/addresses",
        json=address_payload(
            address_line="Second Address",
            city="Chennai",
            pincode="600002",
            is_default=False,
        ),
    )

    assert second_response.status_code == 201

    second_address_id = second_response.json()["id"]

    update_response = client.put(
        f"/addresses/{second_address_id}",
        json={
            "is_default": True,
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["id"] == second_address_id
    assert data["is_default"] is True

    addresses_response = client.get(
        f"/customers/{customer_id}/addresses"
    )

    assert addresses_response.status_code == 200

    addresses = addresses_response.json()

    first_address = next(
        item
        for item in addresses
        if item["id"] == first_address_id
    )

    second_address = next(
        item
        for item in addresses
        if item["id"] == second_address_id
    )

    assert first_address["is_default"] is False
    assert second_address["is_default"] is True


def test_update_nonexistent_address(client):

    response = client.put(
        "/addresses/99999",
        json={
            "city": "Chennai",
        },
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Address not found"
    )


def test_address_validation_address_line_too_short(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    response = client.post(
        f"/customers/{customer_id}/addresses",
        json={
            "address_line": "123",
            "city": "Chennai",
            "pincode": "600001",
            "address_type": "Home",
            "is_default": False,
        },
    )

    assert response.status_code == 422


def test_address_validation_city_too_short(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    response = client.post(
        f"/customers/{customer_id}/addresses",
        json={
            "address_line": "123 Main Street",
            "city": "A",
            "pincode": "600001",
            "address_type": "Home",
            "is_default": False,
        },
    )

    assert response.status_code == 422


def test_address_validation_invalid_pincode(client):

    customer_response = client.post(
        "/customers",
        json=customer_payload(),
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    response = client.post(
        f"/customers/{customer_id}/addresses",
        json={
            "address_line": "123 Main Street",
            "city": "Chennai",
            "pincode": "123",
            "address_type": "Home",
            "is_default": False,
        },
    )

    assert response.status_code == 422