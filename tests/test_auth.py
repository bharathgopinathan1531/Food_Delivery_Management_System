import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


# ============================================================
# TEST DATABASE
# ============================================================

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================
# CLIENT FIXTURE
# ============================================================

@pytest.fixture(scope="function")
def client(db):

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================
# TEST USER DATA
# ============================================================

@pytest.fixture
def user_data():
    return {
        "name": "Test Customer",
        "email": "test.customer@example.com",
        "phone": "9876543210",
        "password": "Test@12345",
        "role": "Customer",
    }


# ============================================================
# REGISTER TESTS
# ============================================================

def test_register_customer(client, user_data):

    response = client.post(
        "/auth/register",
        json=user_data
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Customer"
    assert data["email"] == "test.customer@example.com"
    assert data["phone"] == "9876543210"
    assert data["role"] == "Customer"
    assert data["is_active"] is True

    # Password must never be returned
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client, user_data):

    first_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Email already registered"
    )


def test_register_invalid_role(client, user_data):

    user_data["role"] = "Invalid Role"

    response = client.post(
        "/auth/register",
        json=user_data
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Invalid role"


def test_register_email_is_normalized(client, user_data):

    user_data["email"] = "TEST.CUSTOMER@EXAMPLE.COM"

    response = client.post(
        "/auth/register",
        json=user_data
    )

    assert response.status_code == 201

    assert (
        response.json()["email"]
        == "test.customer@example.com"
    )


# ============================================================
# LOGIN TESTS
# ============================================================

def test_login_success(client, user_data):

    register_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"

    assert isinstance(
        data["access_token"],
        str
    )

    assert data["access_token"]

    assert isinstance(
        data["refresh_token"],
        str
    )

    assert data["refresh_token"]


def test_login_wrong_password(client, user_data):

    register_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "email": user_data["email"],
            "password": "WrongPassword@123",
        },
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "Invalid email or password"
    )


def test_login_unknown_email(client):

    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "Invalid email or password"
    )


# ============================================================
# /AUTH/ME TESTS
# ============================================================

def test_get_me_with_access_token(client, user_data):

    register_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
    assert data["role"] == user_data["role"]


def test_get_me_without_token(client):

    response = client.get("/auth/me")

    assert response.status_code == 401


# ============================================================
# REFRESH TOKEN TESTS
# ============================================================

def test_refresh_token(client, user_data):

    register_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_refresh_with_access_token_is_rejected(
    client,
    user_data
):

    register_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token
        },
    )

    assert response.status_code == 401

    assert (
        response.json()["detail"]
        == "Refresh token required"
    )