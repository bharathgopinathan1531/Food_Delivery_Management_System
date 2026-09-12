from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.menu import MenuItem
from app.models.restaurant import Restaurant
from app.schemas.cart import CartItemCreate, CartItemUpdate


def get_cart(db: Session, customer_id: int):
    return (
        db.query(Cart)
        .filter(Cart.customer_id == customer_id)
        .first()
    )


def get_or_create_cart(db: Session, customer_id: int):
    cart = get_cart(db, customer_id)

    if not cart:
        cart = Cart(
            customer_id=customer_id,
            restaurant_id=None,
            subtotal=0.0,
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


def calculate_subtotal(cart: Cart):
    return round(
        sum(item.subtotal for item in cart.items),
        2
    )


def add_item(
    db: Session,
    customer_id: int,
    item_data: CartItemCreate,
):
    # Check menu item
    menu_item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_data.menu_item_id)
        .first()
    )

    if not menu_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found",
        )

    # Business Rule 1:
    # Unavailable items cannot be added
    if not menu_item.availability:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Menu item is unavailable",
        )

    # Check restaurant
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == menu_item.restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    cart = get_or_create_cart(db, customer_id)

    # Business Rule 2:
    # Cart can contain items from only one restaurant
    if cart.restaurant_id is not None:
        if cart.restaurant_id != menu_item.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart can contain items from only one restaurant",
            )

    # Set restaurant for empty cart
    if cart.restaurant_id is None:
        cart.restaurant_id = menu_item.restaurant_id

    # Check whether item already exists
    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.menu_item_id == item_data.menu_item_id,
        )
        .first()
    )

    if cart_item:
        cart_item.quantity += item_data.quantity
        cart_item.subtotal = round(
            cart_item.quantity * cart_item.unit_price,
            2,
        )
    else:
        unit_price = float(menu_item.price)

        cart_item = CartItem(
            cart_id=cart.id,
            menu_item_id=menu_item.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            subtotal=round(
                unit_price * item_data.quantity,
                2,
            ),
        )

        db.add(cart_item)

    db.flush()

    cart.subtotal = calculate_subtotal(cart)

    db.commit()
    db.refresh(cart)

    return cart


def update_item(
    db: Session,
    customer_id: int,
    item_id: int,
    item_data: CartItemUpdate,
):
    cart = get_cart(db, customer_id)

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    cart_item.quantity = item_data.quantity

    cart_item.subtotal = round(
        cart_item.quantity * cart_item.unit_price,
        2,
    )

    cart.subtotal = calculate_subtotal(cart)

    db.commit()
    db.refresh(cart)

    return cart


def remove_item(
    db: Session,
    customer_id: int,
    item_id: int,
):
    cart = get_cart(db, customer_id)

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    db.delete(cart_item)
    db.flush()

    # Empty cart should no longer belong to a restaurant
    remaining_items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .count()
    )

    if remaining_items == 0:
        cart.restaurant_id = None

    cart.subtotal = calculate_subtotal(cart)

    db.commit()
    db.refresh(cart)

    return cart


def clear_cart(
    db: Session,
    customer_id: int,
):
    cart = get_cart(db, customer_id)

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found",
        )

    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete(
        synchronize_session=False
    )

    cart.restaurant_id = None
    cart.subtotal = 0.0

    db.commit()
    db.refresh(cart)

    return cart