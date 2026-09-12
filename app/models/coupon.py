from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    coupon_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    discount_type = Column(
        String(20),
        nullable=False
    )

    discount_value = Column(
        Float,
        nullable=False
    )

    minimum_order_value = Column(
        Float,
        nullable=False,
        default=0.0
    )

    maximum_discount = Column(
        Float,
        nullable=True
    )

    start_date = Column(
        DateTime(timezone=True),
        nullable=False
    )

    expiry_date = Column(
        DateTime(timezone=True),
        nullable=False
    )

    usage_limit = Column(
        Integer,
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        default="Active"
    )

    usages = relationship(
        "CouponUsage",
        back_populates="coupon",
        cascade="all, delete-orphan"
    )


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    coupon_id = Column(
        Integer,
        ForeignKey("coupons.id"),
        nullable=False,
        index=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    used_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    coupon = relationship(
        "Coupon",
        back_populates="usages"
    )

    __table_args__ = (
        UniqueConstraint(
            "coupon_id",
            "customer_id",
            name="uq_coupon_customer_usage"
        ),
    )