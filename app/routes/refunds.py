from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db

from app.repositories.refund import (
    create_refund,
    get_all_refunds,
    get_refund,
)

from app.schemas.refund import (
    RefundCreate,
    RefundResponse,
)

from app.services.notification_service import (
    notify_refund_processed,
)


router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"]
)


# ---------------------------------------------------------
# POST /refunds/payment/{payment_id}
# Create refund for a payment
# ---------------------------------------------------------
@router.post(
    "/payment/{payment_id}",
    response_model=RefundResponse,
    status_code=201
)
def create_refund_api(
    payment_id: int,
    refund_data: RefundCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    refund = create_refund(
        db=db,
        payment_id=payment_id,
        refund_data=refund_data
    )

    # -----------------------------------------------------
    # Send refund processed notification in background
    # -----------------------------------------------------
    background_tasks.add_task(
        notify_refund_processed,
        refund.order.customer_id,
        refund.order_id,
        refund.amount,
    )

    return refund


# ---------------------------------------------------------
# GET /refunds
# Get all refunds
# ---------------------------------------------------------
@router.get(
    "",
    response_model=list[RefundResponse]
)
def get_refunds_api(
    db: Session = Depends(get_db)
):
    return get_all_refunds(db=db)


# ---------------------------------------------------------
# GET /refunds/{refund_id}
# Get refund by ID
# ---------------------------------------------------------
@router.get(
    "/{refund_id}",
    response_model=RefundResponse
)
def get_refund_api(
    refund_id: int,
    db: Session = Depends(get_db)
):
    return get_refund(
        db=db,
        refund_id=refund_id
    )