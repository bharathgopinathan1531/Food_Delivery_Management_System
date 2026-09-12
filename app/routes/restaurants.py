from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
)

from app.schemas.search import (
    RestaurantSearchParams,
)

from app.services import restaurant_service

from app.repositories.restaurant_repository import (
    search_restaurants,
)

from app.utils.dependencies import (
    get_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"]
)


# ---------------------------------------------------------
# POST /restaurants
# Create restaurant
# ---------------------------------------------------------
@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED
)
def create_restaurant(
    data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Admin",
            "Restaurant Owner"
        )
    )
):
    if (
        current_user.role == "Restaurant Owner"
        and data.owner_id != current_user.id
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Restaurant owners can create restaurants "
                "only for themselves"
            )
        )

    return restaurant_service.create_restaurant(
        db,
        data
    )


# ---------------------------------------------------------
# GET /restaurants
# Get all restaurants
# ---------------------------------------------------------
@router.get(
    "",
    response_model=list[RestaurantResponse]
)
def get_restaurants(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return restaurant_service.get_restaurants(db)


# ---------------------------------------------------------
# GET /restaurants/search
# Search, filter, sort and paginate restaurants
# ---------------------------------------------------------
@router.get(
    "/search",
    response_model=list[RestaurantResponse]
)
def search_restaurants_api(
    params: RestaurantSearchParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return search_restaurants(
        db=db,
        cuisine=params.cuisine,
        city=params.city,
        rating=params.rating,
        status=params.status,
        delivery_time=params.delivery_time,
        page=params.page,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order.value,
    )


# ---------------------------------------------------------
# GET /restaurants/{restaurant_id}
# Get single restaurant
# ---------------------------------------------------------
@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse
)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return restaurant_service.get_restaurant(
        db,
        restaurant_id
    )


# ---------------------------------------------------------
# PUT /restaurants/{restaurant_id}
# Update restaurant
# ---------------------------------------------------------
@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse
)
def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Admin",
            "Restaurant Owner"
        )
    )
):
    restaurant = restaurant_service.get_restaurant(
        db,
        restaurant_id
    )

    if (
        current_user.role == "Restaurant Owner"
        and restaurant.owner_id != current_user.id
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can update only your own restaurant"
        )

    return restaurant_service.update_restaurant(
        db,
        restaurant_id,
        data
    )


# ---------------------------------------------------------
# DELETE /restaurants/{restaurant_id}
# Delete restaurant
# ---------------------------------------------------------
@router.delete(
    "/{restaurant_id}"
)
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "Admin",
            "Restaurant Owner"
        )
    )
):
    restaurant = restaurant_service.get_restaurant(
        db,
        restaurant_id
    )

    if (
        current_user.role == "Restaurant Owner"
        and restaurant.owner_id != current_user.id
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own restaurant"
        )

    return restaurant_service.delete_restaurant(
        db,
        restaurant_id
    )