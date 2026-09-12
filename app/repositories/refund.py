from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.order import Order
from app.models.refund import Refund
from app.schemas.refund import RefundCreate


def create_refund(
    db: Session,
    payment_id: int,
    refund_data: RefundCreate
):
    # Find payment
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    # Find order
    order = (
        db.query(Order)
        .filter(Order.id == payment.order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Calculate already refunded amount
    existing_refunds = (
        db.query(Refund)
        .filter(Refund.payment_id == payment_id)
        .all()
    )

    already_refunded = sum(
        refund.amount for refund in existing_refunds
    )

    remaining_amount = round(
        payment.amount - already_refunded,
        2
    )

    if remaining_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment has already been fully refunded"
        )

    # Create full remaining refund
    refund = Refund(
        payment_id=payment_id,
        order_id=payment.order_id,
        amount=remaining_amount,
        refund_status="Success",
        reason=refund_data.reason,
    )

    db.add(refund)

    # Update payment and order status
    payment.payment_status = "Refunded"
    order.payment_status = "Refunded"

    db.commit()
    db.refresh(refund)

    return refund


def get_all_refunds(db: Session):
    return (
        db.query(Refund)
        .order_by(Refund.refunded_at.desc(), Refund.id.desc())
        .all()
    )


def get_refund(db: Session, refund_id: int):
    refund = (
        db.query(Refund)
        .filter(Refund.id == refund_id)
        .first()
    )

    if not refund:
        raise HTTPException(
            status_code=404,
            detail="Refund not found"
        )

    return refund