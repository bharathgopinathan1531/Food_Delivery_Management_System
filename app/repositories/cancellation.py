from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import Payment
from app.models.cancellation import CancellationHistory
from app.models.refund import Refund
from app.schemas.cancellation import CancellationRequest


def cancel_order(
    db: Session,
    order_id: int,
    cancellation_data: CancellationRequest
):
    # Find order
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Get current order status
    current_status = order.order_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    # Cancellation rules
    if current_status == "Delivered":
        raise HTTPException(
            status_code=400,
            detail="Delivered orders cannot be cancelled"
        )

    if current_status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Order is already cancelled"
        )

    if current_status in ["Ready", "Picked Up", "Out for Delivery"]:
        raise HTTPException(
            status_code=400,
            detail="Order cannot be cancelled at this stage"
        )

    # Determine refund percentage
    if current_status == "Pending":
        refund_percentage = 1.0
    elif current_status == "Accepted":
        refund_percentage = 1.0
    elif current_status == "Preparing":
        refund_percentage = 0.5
    else:
        refund_percentage = 0.0

    # Find payment
    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order_id)
        .first()
    )

    refund_amount = 0.0

    if payment:
        # Calculate already refunded amount
        existing_refunds = (
            db.query(Refund)
            .filter(Refund.payment_id == payment.id)
            .all()
        )

        already_refunded = sum(
            refund.amount for refund in existing_refunds
        )

        remaining_amount = max(
            0.0,
            payment.amount - already_refunded
        )

        refund_amount = round(
            remaining_amount * refund_percentage,
            2
        )

        # Create refund if applicable
        if refund_amount > 0:
            refund = Refund(
                payment_id=payment.id,
                order_id=order_id,
                amount=refund_amount,
                refund_status="Success",
                reason=cancellation_data.reason,
            )

            db.add(refund)

            # Full refund
            if refund_amount >= remaining_amount:
                payment.payment_status = "Refunded"

    # Create cancellation history
    cancellation = CancellationHistory(
        order_id=order_id,
        previous_status=current_status,
        cancellation_reason=cancellation_data.reason,
        refund_amount=refund_amount,
    )

    db.add(cancellation)

    # Update order status
    order.order_status = "Cancelled"

    # Update order payment status
    if refund_amount > 0:
        if payment and refund_amount >= payment.amount:
            order.payment_status = "Refunded"

    db.commit()
    db.refresh(cancellation)

    return order