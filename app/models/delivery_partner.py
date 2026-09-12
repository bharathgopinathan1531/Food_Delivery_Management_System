import enum

from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryPartnerStatus(str, enum.Enum):
    AVAILABLE = "Available"
    BUSY = "Busy"
    OFFLINE = "Offline"


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    phone = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    vehicle_type = Column(
        String(50),
        nullable=False
    )

    vehicle_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    availability_status = Column(
        Enum(DeliveryPartnerStatus),
        nullable=False,
        default=DeliveryPartnerStatus.AVAILABLE
    )

    current_location = Column(
        String(255),
        nullable=True
    )

    orders = relationship(
        "Order",
        back_populates="delivery_partner"
    )