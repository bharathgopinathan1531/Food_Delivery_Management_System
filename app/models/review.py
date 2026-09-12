from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True
    )

    food_item_id = Column(
        Integer,
        ForeignKey("menu_items.id"),
        nullable=True,
        index=True
    )

    delivery_partner_id = Column(
        Integer,
        ForeignKey("delivery_partners.id"),
        nullable=True,
        index=True
    )

    rating = Column(
        Integer,
        nullable=False
    )

    review = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    customer = relationship("Customer")
    order = relationship("Order")
    restaurant = relationship("Restaurant")
    food_item = relationship("MenuItem")
    delivery_partner = relationship("DeliveryPartner")