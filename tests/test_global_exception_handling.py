from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


# ============================================================
# TEST APPLICATION
# ============================================================

app = FastAPI()


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        }
    )


# ============================================================
# TEST ROUTE - UNEXPECTED ERROR
# ============================================================

@app.get("/test-global-error")
def trigger_global_error():
    raise RuntimeError(
        "This is an unexpected internal error"
    )


# ============================================================
# TEST ROUTE - NORMAL REQUEST
# ============================================================

@app.get("/test-success")
def trigger_success():
    return {
        "message": "Success"
    }


# ============================================================
# TEST CLIENT
# ============================================================

client = TestClient(
    app,
    raise_server_exceptions=False
)


# ============================================================
# TEST 1 - GLOBAL EXCEPTION HANDLER
# ============================================================

def test_global_exception_handler():
    response = client.get(
        "/test-global-error"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "Internal server error"
    }


# ============================================================
# TEST 2 - INTERNAL ERROR NOT EXPOSED
# ============================================================

def test_internal_exception_message_is_not_exposed():
    response = client.get(
        "/test-global-error"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Internal server error"
    )

    assert (
        "This is an unexpected internal error"
        not in response.text
    )


# ============================================================
# TEST 3 - NORMAL REQUEST STILL WORKS
# ============================================================

def test_normal_request_is_not_affected():
    response = client.get(
        "/test-success"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Success"
    }