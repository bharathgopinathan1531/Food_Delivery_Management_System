from enum import Enum

from pydantic import BaseModel, Field


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class RestaurantSearchParams(BaseModel):
    cuisine: str | None = None
    city: str | None = None

    rating: float | None = Field(
        default=None,
        ge=0,
        le=5
    )

    status: str | None = None

    # Maximum estimated delivery time in minutes
    delivery_time: int | None = Field(
        default=None,
        gt=0
    )

    page: int = Field(
        default=1,
        ge=1
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100
    )

    sort_by: str = "id"
    sort_order: SortOrder = SortOrder.DESC


class FoodSearchParams(BaseModel):
    category: str | None = None

    min_price: float | None = Field(
        default=None,
        ge=0
    )

    max_price: float | None = Field(
        default=None,
        ge=0
    )

    vegetarian: bool | None = None
    spicy_level: str | None = None
    availability: bool | None = None

    page: int = Field(
        default=1,
        ge=1
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100
    )

    sort_by: str = "id"
    sort_order: SortOrder = SortOrder.DESC


class OrderSearchParams(BaseModel):
    status: str | None = None
    payment_status: str | None = None

    restaurant_id: int | None = Field(
        default=None,
        gt=0
    )

    start_date: str | None = None
    end_date: str | None = None

    page: int = Field(
        default=1,
        ge=1
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100
    )

    sort_by: str = "id"
    sort_order: SortOrder = SortOrder.DESC