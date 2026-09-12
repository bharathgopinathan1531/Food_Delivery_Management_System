import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    CARD = "Card"
    WALLET = "Wallet"
    CASH_ON_DELIVERY = "Cash on Delivery"


class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    SUCCESS = "Success"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        unique=True,
        index=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    payment_method = Column(
        Enum(PaymentMethod),
        nullable=False
    )

    transaction_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    payment_status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING
    )

    paid_at = Column(
        DateTime,
        nullable=True
    )

    # ---------------------------------------------------------
    # Order
    # ---------------------------------------------------------
    order = relationship(
        "Order",
        back_populates="payment"
    )

    # ---------------------------------------------------------
    # Level 11 - Refund History
    # ---------------------------------------------------------
    refunds = relationship(
        "Refund",
        back_populates="payment",
        cascade="all, delete-orphan"
    )