from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_cors_simple_request():
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:3000"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }

    assert "access-control-allow-origin" in response.headers


def test_cors_preflight_request():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 200

    assert response.headers.get(
        "access-control-allow-origin"
    ) == "http://localhost:3000"

    assert response.headers.get(
        "access-control-allow-credentials"
    ) == "true"


def test_cors_allows_methods():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        }
    )

    assert response.status_code == 200

    assert response.headers.get(
        "access-control-allow-origin"
    ) == "http://localhost:3000"