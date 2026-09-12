from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db

from app.repositories.payment import (
    create_payment,
    get_order_payment,
    get_payment,
)

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
)

from app.services.notification_service import (
    notify_payment_success,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# ---------------------------------------------------------
# POST /payments/{order_id}
# Create payment for an order
# ---------------------------------------------------------
@router.post(
    "/{order_id}",
    response_model=PaymentResponse,
    status_code=201
)
def create_payment_api(
    order_id: int,
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    payment = create_payment(
        db=db,
        order_id=order_id,
        payment_data=payment_data
    )

    # -----------------------------------------------------
    # Send payment success notification in background
    # -----------------------------------------------------
    background_tasks.add_task(
        notify_payment_success,
        order_id,
        payment.id,
    )

    return payment


# ---------------------------------------------------------
# GET /payments/{payment_id}
# Get payment by payment ID
# ---------------------------------------------------------
@router.get(
    "/{payment_id}",
    response_model=PaymentResponse
)
def get_payment_api(
    payment_id: int,
    db: Session = Depends(get_db)
):
    return get_payment(
        db=db,
        payment_id=payment_id
    )


# ---------------------------------------------------------
# GET /payments/order/{order_id}
# Get payment for an order
# ---------------------------------------------------------
@router.get(
    "/order/{order_id}",
    response_model=PaymentResponse
)
def get_order_payment_api(
    order_id: int,
    db: Session = Depends(get_db)
):
    return get_order_payment(
        db=db,
        order_id=order_id
    )