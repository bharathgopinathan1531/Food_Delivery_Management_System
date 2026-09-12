from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.repositories import restaurant_repository
from app.repositories import user_repository
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
)


def create_restaurant(
    db: Session,
    data: RestaurantCreate
):
    # ---------------------------------------------------------
    # Check owner exists
    # ---------------------------------------------------------
    owner = user_repository.get_by_id(
        db,
        data.owner_id
    )

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant owner not found"
        )

    # ---------------------------------------------------------
    # Only Restaurant Owner or Admin can own a restaurant
    # ---------------------------------------------------------
    if owner.role not in {
        "Restaurant Owner",
        "Admin"
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only restaurant owners or admins "
                "can create restaurants"
            )
        )

    # ---------------------------------------------------------
    # Create restaurant
    # ---------------------------------------------------------
    restaurant = Restaurant(
        restaurant_name=data.restaurant_name,
        owner_id=data.owner_id,
        address=data.address,
        city=data.city,
        phone=data.phone,
        cuisine_type=data.cuisine_type,
        opening_time=data.opening_time,
        closing_time=data.closing_time,
        status=data.status,
        delivery_radius=data.delivery_radius,
        delivery_time=data.delivery_time,
    )

    return restaurant_repository.create(
        db,
        restaurant
    )


def get_restaurants(
    db: Session
):
    return restaurant_repository.get_all(db)


def get_restaurant(
    db: Session,
    restaurant_id: int
):
    restaurant = restaurant_repository.get_by_id(
        db,
        restaurant_id
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    return restaurant


def update_restaurant(
    db: Session,
    restaurant_id: int,
    data: RestaurantUpdate
):
    restaurant = get_restaurant(
        db,
        restaurant_id
    )

    update_data = data.model_dump(
        exclude_unset=True
    )

    # ---------------------------------------------------------
    # Validate opening and closing time
    # ---------------------------------------------------------
    if (
        "opening_time" in update_data
        and "closing_time" in update_data
    ):
        if update_data["closing_time"] <= update_data["opening_time"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Closing time must be later "
                    "than opening time"
                )
            )

    elif "opening_time" in update_data:
        if (
            restaurant.closing_time
            <= update_data["opening_time"]
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Closing time must be later "
                    "than opening time"
                )
            )

    elif "closing_time" in update_data:
        if (
            update_data["closing_time"]
            <= restaurant.opening_time
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Closing time must be later "
                    "than opening time"
                )
            )

    # ---------------------------------------------------------
    # Apply updates
    # ---------------------------------------------------------
    for field, value in update_data.items():
        setattr(
            restaurant,
            field,
            value
        )

    return restaurant_repository.update(
        db,
        restaurant
    )


def delete_restaurant(
    db: Session,
    restaurant_id: int
):
    restaurant = get_restaurant(
        db,
        restaurant_id
    )

    restaurant_repository.delete(
        db,
        restaurant
    )

    return {
        "message": "Restaurant deleted successfully"
    }