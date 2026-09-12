from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Kept as a database field for compatibility.
    # We intentionally do not create a relationship to User,
    # so existing Level 1 authentication code remains unchanged.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        unique=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    phone = Column(
        String(20),
        nullable=False
    )

    addresses = relationship(
        "Address",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


class Address(Base):
    __tablename__ = "addresses"

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

    address_line = Column(
        String(255),
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False,
        index=True
    )

    pincode = Column(
        String(10),
        nullable=False,
        index=True
    )

    latitude = Column(
        Float,
        nullable=True
    )

    longitude = Column(
        Float,
        nullable=True
    )

    address_type = Column(
        String(30),
        nullable=False,
        default="Home"
    )

    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )

    customer = relationship(
        "Customer",
        back_populates="addresses"
    )