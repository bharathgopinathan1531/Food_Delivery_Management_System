from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(
        self,
        order_id: int,
        websocket: WebSocket
    ):
        await websocket.accept()

        self.active_connections.setdefault(
            order_id,
            []
        ).append(websocket)

    def disconnect(
        self,
        order_id: int,
        websocket: WebSocket
    ):
        connections = self.active_connections.get(
            order_id,
            []
        )

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            self.active_connections.pop(
                order_id,
                None
            )

    async def broadcast(
        self,
        order_id: int,
        message: dict
    ):
        connections = self.active_connections.get(
            order_id,
            []
        )

        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(
                order_id,
                websocket
            )


manager = ConnectionManager()