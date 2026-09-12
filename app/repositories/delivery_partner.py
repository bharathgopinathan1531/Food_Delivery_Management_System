from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerStatus,
)
from app.models.order import Order
from app.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerStatusUpdate,
)
from app.repositories.order_tracking import add_tracking_record


def create_delivery_partner(
    db: Session,
    partner_data: DeliveryPartnerCreate
):
    # ---------------------------------------------------------
    # 1. Check duplicate phone
    # ---------------------------------------------------------
    existing_phone = (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.phone == partner_data.phone
        )
        .first()
    )

    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Delivery partner with this phone already exists"
        )

    # ---------------------------------------------------------
    # 2. Check duplicate vehicle number
    # ---------------------------------------------------------
    existing_vehicle = (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.vehicle_number
            == partner_data.vehicle_number
        )
        .first()
    )

    if existing_vehicle:
        raise HTTPException(
            status_code=400,
            detail="Delivery partner with this vehicle number already exists"
        )

    # ---------------------------------------------------------
    # 3. Create delivery partner
    # ---------------------------------------------------------
    partner = DeliveryPartner(
        name=partner_data.name,
        phone=partner_data.phone,
        vehicle_type=partner_data.vehicle_type,
        vehicle_number=partner_data.vehicle_number,
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location=partner_data.current_location,
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    return partner


def get_delivery_partners(
    db: Session
):
    return (
        db.query(DeliveryPartner)
        .order_by(DeliveryPartner.id.desc())
        .all()
    )


def update_delivery_partner_status(
    db: Session,
    partner_id: int,
    status_data: DeliveryPartnerStatusUpdate
):
    partner = (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.id == partner_id
        )
        .first()
    )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Delivery partner not found"
        )

    allowed_statuses = {
        "Available": DeliveryPartnerStatus.AVAILABLE,
        "Busy": DeliveryPartnerStatus.BUSY,
        "Offline": DeliveryPartnerStatus.OFFLINE,
    }

    new_status = allowed_statuses.get(
        status_data.availability_status
    )

    if not new_status:
        raise HTTPException(
            status_code=400,
            detail="Invalid availability status"
        )

    partner.availability_status = new_status

    db.commit()
    db.refresh(partner)

    return partner


def assign_driver_to_order(
    db: Session,
    order_id: int,
    partner_id: int
):
    # ---------------------------------------------------------
    # 1. Check order
    # ---------------------------------------------------------
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # ---------------------------------------------------------
    # 2. Check delivery partner
    # ---------------------------------------------------------
    partner = (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.id == partner_id
        )
        .first()
    )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Delivery partner not found"
        )

    # ---------------------------------------------------------
    # 3. Only available partners can be assigned
    # ---------------------------------------------------------
    current_status = partner.availability_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    if current_status != "Available":
        raise HTTPException(
            status_code=400,
            detail="Only available delivery partners can be assigned"
        )

    # ---------------------------------------------------------
    # 4. Check order status
    # ---------------------------------------------------------
    order_status = order.order_status

    if hasattr(order_status, "value"):
        order_status = order_status.value

    if order_status in [
        "Delivered",
        "Cancelled"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Driver cannot be assigned to this order"
        )

    # ---------------------------------------------------------
    # 5. Assign driver
    # ---------------------------------------------------------
    order.delivery_partner_id = partner.id

    # Driver becomes busy
    partner.availability_status = DeliveryPartnerStatus.BUSY

    # Order moves to Out for Delivery
    order.order_status = "Out for Delivery"

    # ---------------------------------------------------------
    # 6. Automatically create tracking record
    # ---------------------------------------------------------
    add_tracking_record(
        db=db,
        order_id=order.id,
        status="Out for Delivery",
        location=partner.current_location,
        remarks="Delivery partner assigned and order is out for delivery"
    )

    # ---------------------------------------------------------
    # 7. Save changes
    # ---------------------------------------------------------
    db.commit()
    db.refresh(order)

    return order 