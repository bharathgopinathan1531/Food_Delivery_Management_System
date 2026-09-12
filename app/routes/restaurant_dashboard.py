from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.restaurant import Restaurant

from app.repositories.restaurant_dashboard import (
    get_today_orders,
    get_pending_orders,
    get_completed_orders,
    get_cancelled_orders,
    get_today_revenue,
    get_monthly_revenue,
    get_most_ordered_food,
    get_average_rating,
    get_total_customers,
)

from app.schemas.order import OrderResponse

from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/restaurant-dashboard",
    tags=["Restaurant Dashboard"]
)


# ============================================================
# TODAY'S ORDERS
# ============================================================

@router.get(
    "/{restaurant_id}/today-orders",
    response_model=list[OrderResponse]
)
def get_today_orders_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("Restaurant Owner")
    )
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard"
        )

    return get_today_orders(
        db=db,
        restaurant_id=restaurant_id,
    )
    
@router.get(
    "/{restaurant_id}/completed-orders",
    response_model=list[OrderResponse],
)
def get_completed_orders_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_completed_orders(
        db=db,
        restaurant_id=restaurant_id,
    )
    
@router.get(
    "/{restaurant_id}/today-revenue",
)
def get_today_revenue_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_today_revenue(
        db=db,
        restaurant_id=restaurant_id,
    )
    
@router.get(
    "/{restaurant_id}/monthly-revenue",
)
def get_monthly_revenue_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_monthly_revenue(
        db=db,
        restaurant_id=restaurant_id,
    )
    
@router.get(
    "/{restaurant_id}/most-ordered-food",
)
def get_most_ordered_food_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_most_ordered_food(
        db=db,
        restaurant_id=restaurant_id,
    )
    
@router.get(
    "/{restaurant_id}/total-customers",
)
def get_total_customers_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_total_customers(
        db=db,
        restaurant_id=restaurant_id,
    )
    
    
@router.get(
    "/{restaurant_id}/average-rating",
)
def get_average_rating_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_average_rating(
        db=db,
        restaurant_id=restaurant_id,
    )
    
    
@router.get(
    "/{restaurant_id}/cancelled-orders",
    response_model=list[OrderResponse],
)
def get_cancelled_orders_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Restaurant Owner")),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard",
        )

    return get_cancelled_orders(
        db=db,
        restaurant_id=restaurant_id,
    )


# ============================================================
# PENDING ORDERS
# ============================================================

@router.get(
    "/{restaurant_id}/pending-orders",
    response_model=list[OrderResponse]
)
def get_pending_orders_api(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("Restaurant Owner")
    )
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own restaurant dashboard"
        )

    return get_pending_orders(
        db=db,
        restaurant_id=restaurant_id,
    )