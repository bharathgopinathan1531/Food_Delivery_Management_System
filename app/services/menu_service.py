from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.models.restaurant_staff import RestaurantStaff
from app.repositories import menu_repository
from app.schemas.menu import MenuItemCreate, MenuItemUpdate


def _check_menu_permission(
    db: Session,
    current_user,
    restaurant_id: int
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    # Admin can manage every restaurant
    if current_user.role == "Admin":
        return restaurant

    # Restaurant Owner can manage only their own restaurant
    if current_user.role == "Restaurant Owner":
        if restaurant.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can manage only your own restaurant's menu"
            )

        return restaurant

    # Restaurant Staff can manage only assigned restaurants
    if current_user.role == "Restaurant Staff":
        assignment = (
            db.query(RestaurantStaff)
            .filter(
                RestaurantStaff.restaurant_id == restaurant_id,
                RestaurantStaff.user_id == current_user.id
            )
            .first()
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can manage only your assigned restaurant's menu"
            )

        return restaurant

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to manage restaurant menus"
    )


def create_menu_item(
    db: Session,
    data: MenuItemCreate,
    current_user
):
    _check_menu_permission(
        db,
        current_user,
        data.restaurant_id
    )

    menu_item = MenuItem(
        restaurant_id=data.restaurant_id,
        category=data.category,
        name=data.name,
        description=data.description,
        price=data.price,
        preparation_time=data.preparation_time,
        availability=data.availability,
        vegetarian=data.vegetarian,
        spicy_level=data.spicy_level,
    )

    return menu_repository.create(
        db,
        menu_item
    )


def get_menu_items(
    db: Session,
    restaurant_id: int | None = None
):
    if restaurant_id is not None:
        return menu_repository.get_by_restaurant(
            db,
            restaurant_id
        )

    return menu_repository.get_all(db)


def get_menu_item(
    db: Session,
    menu_item_id: int
):
    menu_item = menu_repository.get_by_id(
        db,
        menu_item_id
    )

    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    return menu_item


def update_menu_item(
    db: Session,
    menu_item_id: int,
    data: MenuItemUpdate,
    current_user
):
    menu_item = get_menu_item(
        db,
        menu_item_id
    )

    _check_menu_permission(
        db,
        current_user,
        menu_item.restaurant_id
    )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            menu_item,
            field,
            value
        )

    return menu_repository.update(
        db,
        menu_item
    )


def delete_menu_item(
    db: Session,
    menu_item_id: int,
    current_user
):
    menu_item = get_menu_item(
        db,
        menu_item_id
    )

    _check_menu_permission(
        db,
        current_user,
        menu_item.restaurant_id
    )

    menu_repository.delete(
        db,
        menu_item
    )

    return {
        "message": "Menu item deleted successfully"
    }