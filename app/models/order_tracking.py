from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class OrderTracking(Base):
    __tablename__ = "order_tracking"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    status = Column(
        String(50),
        nullable=False
    )

    location = Column(
        String(255),
        nullable=True
    )

    remarks = Column(
        String(500),
        nullable=True
    )

    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    order = relationship(
        "Order",
        back_populates="tracking_history"
    )