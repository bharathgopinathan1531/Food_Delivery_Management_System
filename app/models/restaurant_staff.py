from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class RestaurantStaff(Base):
    __tablename__ = "restaurant_staff"

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

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    restaurant = relationship(
        "Restaurant",
        back_populates="staff_members"
    )

    user = relationship(
        "User",
        back_populates="staff_assignments"
    )

    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "user_id",
            name="uq_restaurant_staff"
        ),
    )