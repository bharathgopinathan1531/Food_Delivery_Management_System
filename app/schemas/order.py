from datetime import datetime

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_id: int = Field(..., gt=0)
    restaurant_id: int = Field(..., gt=0)
    address_id: int = Field(..., gt=0)

    delivery_fee: float = Field(
        default=0.0,
        ge=0
    )

    discount: float = Field(
        default=0.0,
        ge=0
    )

    tax: float = Field(
        default=0.0,
        ge=0
    )

    items: list[OrderItemCreate] = Field(
        ...,
        min_length=1
    )


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    delivery_partner_id: int | None
    address_id: int
    subtotal: float
    delivery_fee: float
    discount: float
    tax: float
    total_amount: float
    order_status: str
    payment_status: str
    created_at: datetime
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderCancel(BaseModel):
    reason: str | None = None