from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.admin_analytics import get_total_restaurants
from app.utils.dependencies import require_roles

from app.repositories.admin_analytics import (
    get_total_restaurants,
    get_total_customers,
    get_total_orders,
    get_total_revenue,
    get_total_refunds,
    get_active_delivery_partners,
    get_top_restaurants,
    get_top_food_items,
    get_most_popular_cuisine,
    get_daily_orders,
    get_monthly_revenue,
    get_cancellation_rate,
)


router = APIRouter(
    prefix="/admin-analytics",
    tags=["Admin Analytics"],
)

@router.get("/total-customers")
def get_total_customers_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_total_customers(db=db)


@router.get("/total-restaurants")
def get_total_restaurants_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_total_restaurants(db=db)

@router.get("/total-orders")
def get_total_orders_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_total_orders(db=db)

@router.get("/total-revenue")
def get_total_revenue_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_total_revenue(db=db)

@router.get("/total-refunds")
def get_total_refunds_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_total_refunds(db=db)

@router.get("/active-delivery-partners")
def get_active_delivery_partners_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_active_delivery_partners(db=db)

@router.get("/top-restaurants")
def get_top_restaurants_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_top_restaurants(db=db)

@router.get("/top-food-items")
def get_top_food_items_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_top_food_items(db=db)

@router.get("/most-popular-cuisine")
def get_most_popular_cuisine_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_most_popular_cuisine(db=db)

@router.get("/daily-orders")
def get_daily_orders_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_daily_orders(db=db)


@router.get("/monthly-revenue")
def get_monthly_revenue_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_monthly_revenue(db=db)


@router.get("/cancellation-rate")
def get_cancellation_rate_api(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin")),
):
    return get_cancellation_rate(db=db)