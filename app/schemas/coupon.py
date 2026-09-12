from datetime import datetime

from pydantic import BaseModel, Field


class CouponCreate(BaseModel):
    coupon_code: str = Field(..., min_length=3, max_length=50)

    discount_type: str = Field(
        ...,
        description="Percentage or Fixed"
    )

    discount_value: float = Field(..., gt=0)

    minimum_order_value: float = Field(
        default=0.0,
        ge=0
    )

    maximum_discount: float | None = Field(
        default=None,
        gt=0
    )

    start_date: datetime

    expiry_date: datetime

    usage_limit: int | None = Field(
        default=None,
        gt=0
    )

    status: str = Field(
        default="Active"
    )


class CouponResponse(BaseModel):
    id: int
    coupon_code: str
    discount_type: str
    discount_value: float
    minimum_order_value: float
    maximum_discount: float | None
    start_date: datetime
    expiry_date: datetime
    usage_limit: int | None
    status: str

    class Config:
        from_attributes = True


class CouponApply(BaseModel):
    coupon_code: str = Field(
        ...,
        min_length=3,
        max_length=50
    )

    customer_id: int = Field(
        ...,
        gt=0
    )

    order_value: float = Field(
        ...,
        gt=0
    )


class CouponApplyResponse(BaseModel):
    coupon_code: str
    order_value: float
    discount_amount: float
    final_amount: float