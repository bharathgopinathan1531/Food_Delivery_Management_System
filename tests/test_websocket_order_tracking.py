from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_order_tracking_websocket():
    with client.websocket_connect(
        "/orders/1/ws"
    ) as websocket:

        message = {
            "order_id": 1,
            "status": "Out for Delivery",
            "location": "Chennai"
        }

        websocket.send_json(message)

        received = websocket.receive_json()

        assert received == message


def test_websocket_endpoint_accepts_connection():
    with client.websocket_connect(
        "/orders/999/ws"
    ) as websocket:

        websocket.send_json({
            "order_id": 999,
            "status": "Delivered"
        })

        received = websocket.receive_json()

        assert received["order_id"] == 999
        assert received["status"] == "Delivered"