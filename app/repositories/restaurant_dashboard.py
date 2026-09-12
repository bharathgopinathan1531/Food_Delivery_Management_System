from sqlalchemy import func
from app.models.order import OrderItem
from app.models.menu import MenuItem

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.review import Review


def get_today_orders(
    db: Session,
    restaurant_id: int,
):
    today = datetime.utcnow().date()

    start_of_day = datetime.combine(
        today,
        datetime.min.time()
    )

    end_of_day = start_of_day + timedelta(days=1)

    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_of_day,
            Order.created_at < end_of_day,
        )
        .order_by(
            Order.created_at.desc()
        )
        .all()
    )


# ============================================================
# PENDING ORDERS
# ============================================================

def get_pending_orders(
    db: Session,
    restaurant_id: int,
):
    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == "Pending",
        )
        .order_by(
            Order.created_at.desc()
        )
        .all()
    )
    
def get_completed_orders(db: Session, restaurant_id: int):
    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == "Delivered",
        )
        .order_by(Order.created_at.desc())
        .all()
    )
    
def get_cancelled_orders(db: Session, restaurant_id: int):
    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == "Cancelled",
        )
        .order_by(Order.created_at.desc())
        .all()
    )
    
def get_today_revenue(db: Session, restaurant_id: int):
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    orders = (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == "Delivered",
            Order.created_at >= start_of_day,
            Order.created_at < end_of_day,
        )
        .all()
    )

    total_revenue = sum(
        float(order.total_amount or 0)
        for order in orders
    )

    return {
        "restaurant_id": restaurant_id,
        "date": today.isoformat(),
        "total_revenue": total_revenue,
    }
    
def get_monthly_revenue(db: Session, restaurant_id: int):
    today = datetime.utcnow().date()

    start_of_month = datetime(
        today.year,
        today.month,
        1,
    )

    if today.month == 12:
        start_of_next_month = datetime(
            today.year + 1,
            1,
            1,
        )
    else:
        start_of_next_month = datetime(
            today.year,
            today.month + 1,
            1,
        )

    orders = (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == "Delivered",
            Order.created_at >= start_of_month,
            Order.created_at < start_of_next_month,
        )
        .all()
    )

    total_revenue = sum(
        float(order.total_amount or 0)
        for order in orders
    )

    return {
        "restaurant_id": restaurant_id,
        "month": today.strftime("%Y-%m"),
        "total_revenue": total_revenue,
    }
    
def get_most_ordered_food(db: Session, restaurant_id: int):
    result = (
        db.query(
            MenuItem.id.label("menu_item_id"),
            MenuItem.name.label("food_name"),
            func.sum(OrderItem.quantity).label("total_quantity"),
        )
        .join(
            OrderItem,
            OrderItem.menu_item_id == MenuItem.id,
        )
        .join(
            Order,
            Order.id == OrderItem.order_id,
        )
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == "Delivered",
        )
        .group_by(
            MenuItem.id,
            MenuItem.name,
        )
        .order_by(
            func.sum(OrderItem.quantity).desc()
        )
        .first()
    )

    if not result:
        return {
            "restaurant_id": restaurant_id,
            "menu_item_id": None,
            "food_name": None,
            "total_quantity": 0,
        }

    return {
        "restaurant_id": restaurant_id,
        "menu_item_id": result.menu_item_id,
        "food_name": result.food_name,
        "total_quantity": int(result.total_quantity),
    }
    
  
def get_average_rating(db: Session, restaurant_id: int):
    result = (
        db.query(func.avg(Review.rating))
        .filter(
            Review.restaurant_id == restaurant_id,
        )
        .scalar()
    )

    average_rating = round(float(result), 2) if result is not None else 0.0

    return {
        "restaurant_id": restaurant_id,
        "average_rating": average_rating,
    }
    
def get_total_customers(db: Session, restaurant_id: int):
    total_customers = (
        db.query(func.count(func.distinct(Order.customer_id)))
        .filter(
            Order.restaurant_id == restaurant_id,
        )
        .scalar()
    )

    return {
        "restaurant_id": restaurant_id,
        "total_customers": int(total_customers or 0),
    }