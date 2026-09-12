from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.restaurant import RestaurantStatus


class RestaurantCreate(BaseModel):
    restaurant_name: str = Field(
        min_length=2,
        max_length=100
    )

    owner_id: int

    address: str = Field(
        min_length=5,
        max_length=255
    )

    city: str = Field(
        min_length=2,
        max_length=100
    )

    phone: str = Field(
        min_length=10,
        max_length=20
    )

    cuisine_type: str = Field(
        min_length=2,
        max_length=100
    )

    opening_time: time

    closing_time: time

    status: RestaurantStatus = RestaurantStatus.CLOSED

    delivery_radius: float = Field(
        gt=0
    )

    # Estimated delivery time in minutes
    delivery_time: int = Field(
        gt=0
    )

    @field_validator("closing_time")
    @classmethod
    def validate_closing_time(
        cls,
        value: time,
        info
    ):
        opening_time = info.data.get("opening_time")

        if opening_time is not None and value <= opening_time:
            raise ValueError(
                "Closing time must be later than opening time"
            )

        return value


class RestaurantUpdate(BaseModel):
    restaurant_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    address: str | None = Field(
        default=None,
        min_length=5,
        max_length=255
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=20
    )

    cuisine_type: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    opening_time: time | None = None

    closing_time: time | None = None

    status: RestaurantStatus | None = None

    delivery_radius: float | None = Field(
        default=None,
        gt=0
    )

    # Estimated delivery time in minutes
    delivery_time: int | None = Field(
        default=None,
        gt=0
    )


class RestaurantResponse(BaseModel):
    id: int
    restaurant_name: str
    owner_id: int
    address: str
    city: str
    phone: str
    cuisine_type: str
    opening_time: time
    closing_time: time
    status: RestaurantStatus
    delivery_radius: float
    delivery_time: int

    model_config = ConfigDict(
        from_attributes=True
    )