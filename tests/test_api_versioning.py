from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_api_v1_root():
    response = client.get("/api/v1/")

    assert response.status_code == 404


def test_api_v1_auth_router_exists():
    paths = list(
        app.openapi()["paths"].keys()
    )

    assert any(
        path.startswith("/api/v1/auth")
        for path in paths
    )


def test_api_v1_orders_router_exists():
    paths = list(
        app.openapi()["paths"].keys()
    )

    assert any(
        path.startswith("/api/v1/orders")
        for path in paths
    )


def test_api_v1_restaurants_router_exists():
    paths = list(
        app.openapi()["paths"].keys()
    )

    assert any(
        path.startswith("/api/v1/restaurants")
        for path in paths
    )