from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.schemas.payment import PaymentCreate


ALLOWED_PAYMENT_METHODS = {
    "UPI": PaymentMethod.UPI,
    "Card": PaymentMethod.CARD,
    "Wallet": PaymentMethod.WALLET,
    "Cash on Delivery": PaymentMethod.CASH_ON_DELIVERY,
}


def create_payment(
    db: Session,
    order_id: int,
    payment_data: PaymentCreate,
):
    # ---------------------------------------------------------
    # 1. Check order
    # ---------------------------------------------------------
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    # ---------------------------------------------------------
    # 2. Cancelled orders cannot be paid
    # ---------------------------------------------------------
    order_status = order.order_status

    if hasattr(order_status, "value"):
        order_status = order_status.value

    if order_status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancelled orders cannot be paid",
        )

    # ---------------------------------------------------------
    # 3. Payment amount must match order total
    # ---------------------------------------------------------
    if round(payment_data.amount, 2) != round(
        order.total_amount,
        2,
    ):
        raise HTTPException(
            status_code=400,
            detail="Payment amount must match order total",
        )

    # ---------------------------------------------------------
    # 4. Validate payment method
    # ---------------------------------------------------------
    payment_method = ALLOWED_PAYMENT_METHODS.get(
        payment_data.payment_method
    )

    if not payment_method:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid payment method. "
                "Allowed methods: UPI, Card, Wallet, "
                "Cash on Delivery"
            ),
        )

    # ---------------------------------------------------------
    # 5. Clean transaction ID
    # ---------------------------------------------------------
    transaction_id = payment_data.transaction_id.strip()

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty",
        )

    # ---------------------------------------------------------
    # 6. Prevent duplicate payment for same order
    # ---------------------------------------------------------
    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.order_id == order_id
        )
        .first()
    )

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists for this order",
        )

    # ---------------------------------------------------------
    # 7. Prevent duplicate transaction ID
    # ---------------------------------------------------------
    existing_transaction = (
        db.query(Payment)
        .filter(
            Payment.transaction_id == transaction_id
        )
        .first()
    )

    if existing_transaction:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID already exists",
        )

    # ---------------------------------------------------------
    # 8. Create successful payment
    # ---------------------------------------------------------
    payment = Payment(
        order_id=order_id,
        amount=round(payment_data.amount, 2),
        payment_method=payment_method,
        transaction_id=transaction_id,
        payment_status=PaymentStatus.SUCCESS,
        paid_at=datetime.utcnow(),
    )

    db.add(payment)

    # ---------------------------------------------------------
    # 9. Update order payment status
    # ---------------------------------------------------------
    order.payment_status = "Paid"

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Transaction ID already exists",
        )

    db.refresh(payment)

    return payment


def get_payment(
    db: Session,
    payment_id: int,
):
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


def get_order_payment(
    db: Session,
    order_id: int,
):
    # ---------------------------------------------------------
    # 1. Check order
    # ---------------------------------------------------------
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    # ---------------------------------------------------------
    # 2. Get payment
    # ---------------------------------------------------------
    payment = (
        db.query(Payment)
        .filter(
            Payment.order_id == order_id
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found for this order",
        )

    return payment