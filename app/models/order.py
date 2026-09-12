import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    PREPARING = "Preparing"
    READY = "Ready"
    PICKED_UP = "Picked Up"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class Order(Base):
    __tablename__ = "orders"

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

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True
    )

    delivery_partner_id = Column(
        Integer,
        ForeignKey("delivery_partners.id"),
        nullable=True,
        index=True
    )

    address_id = Column(
        Integer,
        ForeignKey("addresses.id"),
        nullable=False,
        index=True
    )

    subtotal = Column(
        Float,
        nullable=False,
        default=0.0
    )

    delivery_fee = Column(
        Float,
        nullable=False,
        default=0.0
    )

    discount = Column(
        Float,
        nullable=False,
        default=0.0
    )

    tax = Column(
        Float,
        nullable=False,
        default=0.0
    )

    total_amount = Column(
        Float,
        nullable=False,
        default=0.0
    )

    order_status = Column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING
    )

    payment_status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # ---------------------------------------------------------
    # Order Items
    # ---------------------------------------------------------
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    # ---------------------------------------------------------
    # Order Tracking
    # ---------------------------------------------------------
    tracking_history = relationship(
        "OrderTracking",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderTracking.timestamp"
    )

    # ---------------------------------------------------------
    # Delivery Partner
    # ---------------------------------------------------------
    delivery_partner = relationship(
        "DeliveryPartner",
        back_populates="orders"
    )

    # ---------------------------------------------------------
    # Payment
    # ---------------------------------------------------------
    payment = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # ---------------------------------------------------------
    # Level 11 - Cancellation History
    # ---------------------------------------------------------
    cancellation_history = relationship(
        "CancellationHistory",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    # ---------------------------------------------------------
    # Level 11 - Refund History
    # ---------------------------------------------------------
    refunds = relationship(
        "Refund",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

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

    menu_item_id = Column(
        Integer,
        ForeignKey("menu_items.id"),
        nullable=False,
        index=True
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    unit_price = Column(
        Float,
        nullable=False
    )

    subtotal = Column(
        Float,
        nullable=False
    )

    order = relationship(
        "Order",
        back_populates="items"
    )