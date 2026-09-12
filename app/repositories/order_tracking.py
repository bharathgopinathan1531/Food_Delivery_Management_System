from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_tracking import OrderTracking
from app.schemas.order_tracking import OrderTrackingCreate


def add_tracking_record(
    db: Session,
    order_id: int,
    status: str,
    location: str | None = None,
    remarks: str | None = None,
):
    tracking = OrderTracking(
        order_id=order_id,
        status=status,
        location=location,
        remarks=remarks,
    )

    db.add(tracking)
    db.flush()

    return tracking


def create_tracking(
    db: Session,
    order_id: int,
    tracking_data: OrderTrackingCreate
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    current_status = order.order_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    if current_status == "Delivered":
        raise HTTPException(
            status_code=400,
            detail="Completed orders cannot receive tracking updates"
        )

    if current_status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancelled orders cannot receive tracking updates"
        )

    tracking = add_tracking_record(
        db=db,
        order_id=order_id,
        status=tracking_data.status,
        location=tracking_data.location,
        remarks=tracking_data.remarks,
    )

    db.commit()
    db.refresh(tracking)

    return tracking


def get_tracking_history(db: Session, order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return (
        db.query(OrderTracking)
        .filter(OrderTracking.order_id == order_id)
        .order_by(
            OrderTracking.timestamp.asc(),
            OrderTracking.id.asc()
        )
        .all()
    )