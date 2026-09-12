from datetime import datetime

from pydantic import BaseModel, Field


class OrderTrackingCreate(BaseModel):
    status: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    location: str | None = Field(
        default=None,
        max_length=255
    )

    remarks: str | None = Field(
        default=None,
        max_length=500
    )


class OrderTrackingResponse(BaseModel):
    id: int
    order_id: int
    status: str
    location: str | None
    remarks: str | None
    timestamp: datetime

    class Config:
        from_attributes = True