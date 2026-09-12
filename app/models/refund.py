from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    refund_status = Column(
        String(30),
        nullable=False,
        default="Success"
    )

    reason = Column(
        String(500),
        nullable=True
    )

    refunded_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    payment = relationship(
        "Payment",
        back_populates="refunds"
    )

    order = relationship(
        "Order",
        back_populates="refunds"
    )