from pydantic import BaseModel, Field


class DeliveryPartnerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    vehicle_type: str = Field(..., min_length=2, max_length=50)
    vehicle_number: str = Field(..., min_length=2, max_length=50)
    current_location: str | None = Field(
        default=None,
        max_length=255
    )


class DeliveryPartnerResponse(BaseModel):
    id: int
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    availability_status: str
    current_location: str | None

    class Config:
        from_attributes = True


class DeliveryPartnerStatusUpdate(BaseModel):
    availability_status: str = Field(
        ...,
        description="Available, Busy, or Offline"
    )