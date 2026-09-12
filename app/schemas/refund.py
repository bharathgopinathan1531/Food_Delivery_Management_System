from datetime import datetime

from pydantic import BaseModel, Field


class RefundCreate(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500
    )


class RefundResponse(BaseModel):
    id: int
    payment_id: int
    order_id: int
    amount: float
    refund_status: str
    reason: str | None
    refunded_at: datetime

    class Config:
        from_attributes = True