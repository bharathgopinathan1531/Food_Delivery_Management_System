from pydantic import BaseModel, ConfigDict, Field

from app.models.menu import SpicyLevel


class MenuItemCreate(BaseModel):
    restaurant_id: int

    category: str = Field(
        min_length=2,
        max_length=100
    )

    name: str = Field(
        min_length=2,
        max_length=100
    )

    description: str | None = None

    price: float = Field(
        gt=0
    )

    preparation_time: int = Field(
        gt=0
    )

    availability: bool = True

    vegetarian: bool = False

    spicy_level: SpicyLevel = SpicyLevel.MILD


class MenuItemUpdate(BaseModel):
    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    description: str | None = None

    price: float | None = Field(
        default=None,
        gt=0
    )

    preparation_time: int | None = Field(
        default=None,
        gt=0
    )

    availability: bool | None = None

    vegetarian: bool | None = None

    spicy_level: SpicyLevel | None = None


class MenuItemResponse(BaseModel):
    id: int
    restaurant_id: int
    category: str
    name: str
    description: str | None
    price: float
    preparation_time: int
    availability: bool
    vegetarian: bool
    spicy_level: SpicyLevel

    model_config = ConfigDict(
        from_attributes=True
    )