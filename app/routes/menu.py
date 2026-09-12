from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.menu import (
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
)

from app.schemas.search import FoodSearchParams

from app.services.menu_service import (
    create_menu_item,
    delete_menu_item,
    get_menu_item,
    get_menu_items,
    update_menu_item,
)

from app.repositories.menu_repository import search_menu_items

from app.utils.dependencies import (
    get_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/menu",
    tags=["Menu Management"],
)


# ============================================================
# CREATE MENU ITEM
# ============================================================

@router.post(
    "/items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(
                "Admin",
                "Restaurant Owner",
                "Restaurant Staff",
            )
        )
    ],
)
def create_item(
    data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_menu_item(
        db,
        data,
        current_user,
    )


# ============================================================
# GET ALL MENU ITEMS
# ============================================================

@router.get(
    "/items",
    response_model=list[MenuItemResponse],
)
def get_items(
    restaurant_id: int | None = Query(
        default=None,
        description="Filter menu items by restaurant ID",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_menu_items(
        db,
        restaurant_id,
    )


# ============================================================
# FOOD SEARCH, FILTERING & PAGINATION
# ============================================================

@router.get(
    "/search",
    response_model=list[MenuItemResponse],
)
def search_items(
    params: FoodSearchParams = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return search_menu_items(
        db=db,
        category=params.category,
        min_price=params.min_price,
        max_price=params.max_price,
        vegetarian=params.vegetarian,
        spicy_level=params.spicy_level,
        availability=params.availability,
        page=params.page,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order.value,
    )


# ============================================================
# GET MENU ITEM BY ID
# ============================================================

@router.get(
    "/items/{menu_item_id}",
    response_model=MenuItemResponse,
)
def get_item(
    menu_item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_menu_item(
        db,
        menu_item_id,
    )


# ============================================================
# UPDATE MENU ITEM
# ============================================================

@router.put(
    "/items/{menu_item_id}",
    response_model=MenuItemResponse,
    dependencies=[
        Depends(
            require_roles(
                "Admin",
                "Restaurant Owner",
                "Restaurant Staff",
            )
        )
    ],
)
def update_item(
    menu_item_id: int,
    data: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_menu_item(
        db,
        menu_item_id,
        data,
        current_user,
    )


# ============================================================
# DELETE MENU ITEM
# ============================================================

@router.delete(
    "/items/{menu_item_id}",
)
def delete_item(
    menu_item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_menu_item(
        db,
        menu_item_id,
        current_user,
    )