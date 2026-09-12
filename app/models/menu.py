import enum

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class SpicyLevel(str, enum.Enum):
    MILD = "Mild"
    MEDIUM = "Medium"
    HOT = "Hot"
    EXTRA_HOT = "Extra Hot"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True
    )

    category = Column(
        String(100),
        nullable=False,
        index=True
    )

    name = Column(
        String(100),
        nullable=False,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    price = Column(
        Float,
        nullable=False
    )

    preparation_time = Column(
        Integer,
        nullable=False
    )

    availability = Column(
        Boolean,
        nullable=False,
        default=True
    )

    vegetarian = Column(
        Boolean,
        nullable=False,
        default=False
    )

    spicy_level = Column(
        Enum(SpicyLevel),
        nullable=False,
        default=SpicyLevel.MILD
    )

    restaurant = relationship(
        "Restaurant",
        back_populates="menu_items"
    )