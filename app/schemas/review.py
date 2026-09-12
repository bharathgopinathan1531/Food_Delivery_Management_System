from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    customer_id: int = Field(gt=0)
    order_id: int = Field(gt=0)
    restaurant_id: int = Field(gt=0)

    food_item_id: int | None = Field(
        default=None,
        gt=0
    )

    delivery_partner_id: int | None = Field(
        default=None,
        gt=0
    )

    rating: int = Field(
        ge=1,
        le=5
    )

    review: str | None = Field(
        default=None,
        max_length=1000
    )


class ReviewResponse(BaseModel):
    id: int
    customer_id: int
    order_id: int
    restaurant_id: int
    food_item_id: int | None
    delivery_partner_id: int | None
    rating: int
    review: str | None
    created_at: datetime

    class Config:
        from_attributes = True