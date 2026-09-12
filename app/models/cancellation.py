from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class CancellationHistory(Base):
    __tablename__ = "cancellation_history"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    previous_status = Column(
        String(50),
        nullable=False
    )

    cancellation_reason = Column(
        String(500),
        nullable=True
    )

    refund_amount = Column(
        Float,
        nullable=False,
        default=0.0
    )

    cancelled_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    order = relationship(
        "Order",
        back_populates="cancellation_history"
    )