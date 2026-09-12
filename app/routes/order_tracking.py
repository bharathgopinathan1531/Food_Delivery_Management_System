from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.order_tracking import (
    create_tracking,
    get_tracking_history,
)
from app.schemas.order_tracking import (
    OrderTrackingCreate,
    OrderTrackingResponse,
)


router = APIRouter(
    prefix="/orders",
    tags=["Order Tracking"],
)


@router.post(
    "/{order_id}/tracking",
    response_model=OrderTrackingResponse,
    status_code=201
)
def create_tracking_api(
    order_id: int,
    tracking_data: OrderTrackingCreate,
    db: Session = Depends(get_db),
):
    return create_tracking(
        db=db,
        order_id=order_id,
        tracking_data=tracking_data
    )


@router.get(
    "/{order_id}/tracking",
    response_model=list[OrderTrackingResponse]
)
def get_tracking_history_api(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_tracking_history(
        db=db,
        order_id=order_id
    )
    
@router.websocket(
    "/{order_id}/ws"
)
async def order_tracking_websocket(
    websocket: WebSocket,
    order_id: int,
):
    await manager.connect(
        order_id=order_id,
        websocket=websocket
    )

    try:
        while True:
            message = await websocket.receive_json()

            await manager.broadcast(
                order_id=order_id,
                message=message
            )

    except WebSocketDisconnect:
        manager.disconnect(
            order_id=order_id,
            websocket=websocket
        )    