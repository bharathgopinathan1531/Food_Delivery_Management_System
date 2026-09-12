from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.models.customer import Customer
from app.models.order import Order, OrderStatus, OrderItem
from app.models.menu import MenuItem
from app.models.refund import Refund

from app.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerStatus,
)

def get_total_restaurants(db: Session):
    total_restaurants = (
        db.query(func.count(Restaurant.id))
        .scalar()
    )

    return {
        "total_restaurants": int(total_restaurants or 0),
    }
    
def get_total_customers(db: Session):
    total_customers = (
        db.query(func.count(Customer.id))
        .scalar()
    )

    return {
        "total_customers": int(total_customers or 0),
    }
    
def get_total_orders(db: Session):
    total_orders = (
        db.query(func.count(Order.id))
        .scalar()
    )

    return {
        "total_orders": int(total_orders or 0),
    }
    
def get_total_revenue(db: Session):
    total_revenue = (
        db.query(func.sum(Order.total_amount))
        .scalar()
    )

    return {
        "total_revenue": float(total_revenue or 0),
    }
    
def get_total_refunds(db: Session):
    total_refunds = (
        db.query(func.sum(Refund.amount))
        .scalar()
    )

    return {
        "total_refunds": float(total_refunds or 0),
    }
    
def get_active_delivery_partners(db: Session):
    active_delivery_partners = (
        db.query(func.count(DeliveryPartner.id))
        .filter(
            DeliveryPartner.availability_status
            == DeliveryPartnerStatus.AVAILABLE
        )
        .scalar()
    )

    return {
        "active_delivery_partners": int(
            active_delivery_partners or 0
        ),
    }
    
def get_top_restaurants(db: Session):
    top_restaurants = (
        db.query(
            Restaurant.id,
            Restaurant.restaurant_name,
            func.count(Order.id).label("total_orders"),
        )
        .join(
            Order,
            Order.restaurant_id == Restaurant.id,
        )
        .filter(
            Order.order_status == OrderStatus.DELIVERED
        )
        .group_by(
            Restaurant.id,
            Restaurant.restaurant_name,
        )
        .order_by(
            func.count(Order.id).desc()
        )
        .limit(5)
        .all()
    )

    return {
        "top_restaurants": [
            {
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.restaurant_name,
                "total_orders": int(restaurant.total_orders),
            }
            for restaurant in top_restaurants
        ]
    }
    
def get_top_food_items(db: Session):
    top_food_items = (
        db.query(
            MenuItem.id,
            MenuItem.name,
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
            Order.order_status == OrderStatus.DELIVERED
        )
        .group_by(
            MenuItem.id,
            MenuItem.name,
        )
        .order_by(
            func.sum(OrderItem.quantity).desc()
        )
        .limit(5)
        .all()
    )

    return {
        "top_food_items": [
            {
                "menu_item_id": item.id,
                "food_name": item.name,
                "total_quantity": int(item.total_quantity or 0),
            }
            for item in top_food_items
        ]
    }
    
def get_most_popular_cuisine(db: Session):
    most_popular_cuisine = (
        db.query(
            Restaurant.cuisine_type,
            func.count(Order.id).label("total_orders"),
        )
        .join(
            Order,
            Order.restaurant_id == Restaurant.id,
        )
        .filter(
            Order.order_status == OrderStatus.DELIVERED
        )
        .group_by(
            Restaurant.cuisine_type
        )
        .order_by(
            func.count(Order.id).desc()
        )
        .first()
    )

    if not most_popular_cuisine:
        return {
            "cuisine_type": None,
            "total_orders": 0,
        }

    return {
        "cuisine_type": most_popular_cuisine.cuisine_type,
        "total_orders": int(most_popular_cuisine.total_orders),
    }
    
# =========================================================
# STEP 10 - DAILY ORDERS
# =========================================================

def get_daily_orders(db: Session):
    daily_orders = (
        db.query(
            func.date(Order.created_at).label("order_date"),
            func.count(Order.id).label("total_orders"),
        )
        .group_by(
            func.date(Order.created_at)
        )
        .order_by(
            func.date(Order.created_at)
        )
        .all()
    )

    return {
        "daily_orders": [
            {
                "date": str(order.order_date),
                "total_orders": int(order.total_orders),
            }
            for order in daily_orders
        ]
    }
    
# =========================================================
# STEP 11 - MONTHLY REVENUE
# =========================================================

def get_monthly_revenue(db: Session):
    monthly_revenue = (
        db.query(
            func.strftime(
                "%Y-%m",
                Order.created_at
            ).label("month"),
            func.sum(
                Order.total_amount
            ).label("total_revenue"),
        )
        .group_by(
            func.strftime(
                "%Y-%m",
                Order.created_at
            )
        )
        .order_by(
            func.strftime(
                "%Y-%m",
                Order.created_at
            )
        )
        .all()
    )

    return {
        "monthly_revenue": [
            {
                "month": str(revenue.month),
                "total_revenue": float(
                    revenue.total_revenue or 0
                ),
            }
            for revenue in monthly_revenue
        ]
    }
    
# =========================================================
# STEP 12 - CANCELLATION RATE
# =========================================================

def get_cancellation_rate(db: Session):
    total_orders = (
        db.query(func.count(Order.id))
        .scalar()
    )

    cancelled_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.order_status == OrderStatus.CANCELLED
        )
        .scalar()
    )

    total_orders = int(total_orders or 0)
    cancelled_orders = int(cancelled_orders or 0)

    if total_orders == 0:
        cancellation_rate = 0.0
    else:
        cancellation_rate = (
            cancelled_orders / total_orders
        ) * 100

    return {
        "total_orders": total_orders,
        "cancelled_orders": cancelled_orders,
        "cancellation_rate": round(
            cancellation_rate,
            2
        ),
    }