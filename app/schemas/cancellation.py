from datetime import datetime

from pydantic import BaseModel, Field


class CancellationRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500
    )


class CancellationResponse(BaseModel):
    id: int
    order_id: int
    previous_status: str
    cancellation_reason: str | None
    refund_amount: float
    cancelled_at: datetime

    class Config:
        from_attributes = True