from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.coupon import Coupon, CouponUsage
from app.schemas.coupon import CouponApply, CouponCreate


def create_coupon(
    db: Session,
    coupon_data: CouponCreate
):
    existing_coupon = (
        db.query(Coupon)
        .filter(Coupon.coupon_code == coupon_data.coupon_code)
        .first()
    )

    if existing_coupon:
        raise HTTPException(
            status_code=400,
            detail="Coupon code already exists"
        )

    if coupon_data.expiry_date <= coupon_data.start_date:
        raise HTTPException(
            status_code=400,
            detail="Expiry date must be after start date"
        )

    if coupon_data.discount_type not in ["Percentage", "Fixed"]:
        raise HTTPException(
            status_code=400,
            detail="Discount type must be Percentage or Fixed"
        )

    coupon = Coupon(
        coupon_code=coupon_data.coupon_code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        minimum_order_value=coupon_data.minimum_order_value,
        maximum_discount=coupon_data.maximum_discount,
        start_date=coupon_data.start_date,
        expiry_date=coupon_data.expiry_date,
        usage_limit=coupon_data.usage_limit,
        status=coupon_data.status,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return coupon


def get_coupons(db: Session):
    return db.query(Coupon).order_by(Coupon.id.desc()).all()


def apply_coupon(
    db: Session,
    coupon_data: CouponApply
):
    coupon = (
        db.query(Coupon)
        .filter(Coupon.coupon_code == coupon_data.coupon_code)
        .first()
    )

    if not coupon:
        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    now = datetime.now(timezone.utc)

    start_date = coupon.start_date
    expiry_date = coupon.expiry_date

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)

    if now < start_date:
        raise HTTPException(
            status_code=400,
            detail="Coupon is not active yet"
        )

    if now > expiry_date:
        raise HTTPException(
            status_code=400,
            detail="Coupon has expired"
        )

    if coupon.status != "Active":
        raise HTTPException(
            status_code=400,
            detail="Coupon is inactive"
        )

    if coupon_data.order_value < coupon.minimum_order_value:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Minimum order value is "
                f"{coupon.minimum_order_value}"
            )
        )

    previous_usage = (
        db.query(CouponUsage)
        .filter(
            CouponUsage.coupon_id == coupon.id,
            CouponUsage.customer_id == coupon_data.customer_id
        )
        .first()
    )

    if previous_usage:
        raise HTTPException(
            status_code=400,
            detail="Coupon already used by this customer"
        )

    total_usage = (
        db.query(CouponUsage)
        .filter(CouponUsage.coupon_id == coupon.id)
        .count()
    )

    if (
        coupon.usage_limit is not None
        and total_usage >= coupon.usage_limit
    ):
        raise HTTPException(
            status_code=400,
            detail="Coupon usage limit exceeded"
        )

    if coupon.discount_type == "Percentage":
        discount_amount = (
            coupon_data.order_value
            * coupon.discount_value
            / 100
        )

        if (
            coupon.maximum_discount is not None
            and discount_amount > coupon.maximum_discount
        ):
            discount_amount = coupon.maximum_discount

    else:
        discount_amount = coupon.discount_value

    discount_amount = min(
        discount_amount,
        coupon_data.order_value
    )

    final_amount = (
        coupon_data.order_value - discount_amount
    )

    usage = CouponUsage(
        coupon_id=coupon.id,
        customer_id=coupon_data.customer_id,
        used_at=datetime.now(timezone.utc),
    )

    db.add(usage)
    db.commit()

    return {
        "coupon_code": coupon.coupon_code,
        "order_value": coupon_data.order_value,
        "discount_amount": round(discount_amount, 2),
        "final_amount": round(final_amount, 2),
    }