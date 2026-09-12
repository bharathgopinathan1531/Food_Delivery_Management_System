from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.coupon import (
    apply_coupon,
    create_coupon,
    get_coupons,
)
from app.schemas.coupon import (
    CouponApply,
    CouponApplyResponse,
    CouponCreate,
    CouponResponse,
)


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"],
)


@router.post(
    "",
    response_model=CouponResponse,
    status_code=201
)
def create_coupon_api(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
):
    return create_coupon(
        db=db,
        coupon_data=coupon_data,
    )


@router.get(
    "",
    response_model=list[CouponResponse]
)
def get_coupons_api(
    db: Session = Depends(get_db),
):
    return get_coupons(db=db)


@router.post(
    "/apply",
    response_model=CouponApplyResponse
)
def apply_coupon_api(
    coupon_data: CouponApply,
    db: Session = Depends(get_db),
):
    return apply_coupon(
        db=db,
        coupon_data=coupon_data,
    )