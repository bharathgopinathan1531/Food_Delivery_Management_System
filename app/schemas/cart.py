from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int | None
    subtotal: float
    items: list[CartItemResponse] = []

    class Config:
        from_attributes = True