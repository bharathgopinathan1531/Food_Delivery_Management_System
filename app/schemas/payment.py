from datetime import datetime

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    amount: float = Field(
        ...,
        gt=0,
        description="Payment amount must be greater than 0"
    )

    payment_method: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="UPI, Card, Wallet, or Cash on Delivery"
    )

    transaction_id: str = Field(
        ...,
        min_length=3,
        max_length=100
    )


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    transaction_id: str
    payment_status: str
    paid_at: datetime | None

    class Config:
        from_attributes = True