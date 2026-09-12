from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.delivery_partner import (
    create_delivery_partner,
    get_delivery_partners,
    update_delivery_partner_status,
)
from app.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerResponse,
    DeliveryPartnerStatusUpdate,
)


router = APIRouter(
    prefix="/delivery-partners",
    tags=["Delivery Partners"],
)


@router.post(
    "",
    response_model=DeliveryPartnerResponse,
    status_code=201
)
def create_delivery_partner_api(
    partner_data: DeliveryPartnerCreate,
    db: Session = Depends(get_db),
):
    return create_delivery_partner(
        db=db,
        partner_data=partner_data
    )


@router.get(
    "",
    response_model=list[DeliveryPartnerResponse]
)
def get_delivery_partners_api(
    db: Session = Depends(get_db),
):
    return get_delivery_partners(db=db)


@router.put(
    "/{partner_id}/status",
    response_model=DeliveryPartnerResponse
)
def update_delivery_partner_status_api(
    partner_id: int,
    status_data: DeliveryPartnerStatusUpdate,
    db: Session = Depends(get_db),
):
    return update_delivery_partner_status(
        db=db,
        partner_id=partner_id,
        status_data=status_data
    )