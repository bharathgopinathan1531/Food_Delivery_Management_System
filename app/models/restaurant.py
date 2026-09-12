import enum

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from app.database import Base


class RestaurantStatus(str, enum.Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    BUSY = "Busy"
    TEMPORARILY_UNAVAILABLE = "Temporarily Unavailable"


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    restaurant_name = Column(
        String(100),
        nullable=False,
        index=True
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    address = Column(
        String(255),
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False
    )

    phone = Column(
        String(20),
        nullable=False
    )

    cuisine_type = Column(
        String(100),
        nullable=False
    )

    opening_time = Column(
        Time,
        nullable=False
    )

    closing_time = Column(
        Time,
        nullable=False
    )

    status = Column(
        Enum(RestaurantStatus),
        nullable=False,
        default=RestaurantStatus.CLOSED
    )

    delivery_radius = Column(
        Float,
        nullable=False
    )

    # Estimated delivery time in minutes
    delivery_time = Column(
        Integer,
        nullable=False,
        default=30
    )

    # Soft delete flag
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # ---------------------------------------------------------
    # Restaurant owner relationship
    # ---------------------------------------------------------
    owner = relationship(
        "User",
        back_populates="restaurants"
    )

    # ---------------------------------------------------------
    # Restaurant menu relationship
    # ---------------------------------------------------------
    menu_items = relationship(
        "MenuItem",
        back_populates="restaurant",
        cascade="all, delete-orphan"
    )

    # ---------------------------------------------------------
    # Restaurant staff assignments
    # ---------------------------------------------------------
    staff_members = relationship(
        "RestaurantStaff",
        back_populates="restaurant",
        cascade="all, delete-orphan"
    )