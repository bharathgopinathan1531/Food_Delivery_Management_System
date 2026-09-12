from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.models.menu import MenuItem
from app.models.customer import Customer, Address
from app.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerStatus,
)
from app.schemas.order import OrderCreate
from app.repositories.order_tracking import add_tracking_record


def create_order(
    db: Session,
    order_data: OrderCreate
):
    # ---------------------------------------------------------
    # 1. Check customer
    # ---------------------------------------------------------
    customer = (
        db.query(Customer)
        .filter(Customer.id == order_data.customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # ---------------------------------------------------------
    # 2. Check restaurant
    # ---------------------------------------------------------
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == order_data.restaurant_id)
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    # ---------------------------------------------------------
    # 3. Restaurant must be open
    # ---------------------------------------------------------
    restaurant_status = restaurant.status

    if hasattr(restaurant_status, "value"):
        restaurant_status = restaurant_status.value

    if str(restaurant_status).lower() not in [
        "open",
        "active"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Restaurant is closed"
        )

    # ---------------------------------------------------------
    # 4. Check customer delivery addresses
    # ---------------------------------------------------------
    customer_addresses = (
        db.query(Address)
        .filter(
            Address.customer_id == order_data.customer_id
        )
        .all()
    )

    if not customer_addresses:
        raise HTTPException(
            status_code=400,
            detail="Customer has no valid delivery address"
        )

    # ---------------------------------------------------------
    # 5. Check selected delivery address
    # ---------------------------------------------------------
    address = (
        db.query(Address)
        .filter(
            Address.id == order_data.address_id,
            Address.customer_id == order_data.customer_id
        )
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=400,
            detail="Address is invalid"
        )

    # ---------------------------------------------------------
    # 6. Validate delivery address
    # ---------------------------------------------------------
    if (
        not address.address_line
        or not address.city
        or not address.pincode
    ):
        raise HTTPException(
            status_code=400,
            detail="Customer has no valid delivery address"
        )

    # ---------------------------------------------------------
    # 7. Validate food items
    # ---------------------------------------------------------
    subtotal = 0.0
    order_items = []

    for item_data in order_data.items:

        menu_item = (
            db.query(MenuItem)
            .filter(
                MenuItem.id == item_data.menu_item_id
            )
            .first()
        )

        if not menu_item:
            raise HTTPException(
                status_code=404,
                detail="Food item not found"
            )

        if menu_item.restaurant_id != order_data.restaurant_id:
            raise HTTPException(
                status_code=400,
                detail="Food item does not belong to this restaurant"
            )

        if not menu_item.availability:
            raise HTTPException(
                status_code=400,
                detail="Food item is unavailable"
            )

        item_subtotal = (
            menu_item.price * item_data.quantity
        )

        subtotal += item_subtotal

        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                quantity=item_data.quantity,
                unit_price=menu_item.price,
                subtotal=round(item_subtotal, 2)
            )
        )

    # ---------------------------------------------------------
    # 8. Calculate discount
    # ---------------------------------------------------------
    discount = min(
        order_data.discount,
        subtotal
    )

    # ---------------------------------------------------------
    # 9. Calculate total
    # ---------------------------------------------------------
    total_amount = (
        subtotal
        + order_data.tax
        + order_data.delivery_fee
        - discount
    )

    # ---------------------------------------------------------
    # 10. Create order
    # ---------------------------------------------------------
    order = Order(
        customer_id=order_data.customer_id,
        restaurant_id=order_data.restaurant_id,
        address_id=order_data.address_id,
        subtotal=round(subtotal, 2),
        delivery_fee=round(
            order_data.delivery_fee,
            2
        ),
        discount=round(
            discount,
            2
        ),
        tax=round(
            order_data.tax,
            2
        ),
        total_amount=round(
            total_amount,
            2
        )
    )

    db.add(order)
    db.flush()

    # ---------------------------------------------------------
    # 11. Attach order items
    # ---------------------------------------------------------
    for item in order_items:
        item.order_id = order.id
        db.add(item)

    # ---------------------------------------------------------
    # 12. Automatically create Pending tracking
    # ---------------------------------------------------------
    add_tracking_record(
        db=db,
        order_id=order.id,
        status="Pending",
        location=restaurant.restaurant_name,
        remarks="Order placed successfully"
    )

    db.commit()
    db.refresh(order)

    return order


def accept_order(
    db: Session,
    order_id: int
):
    # ---------------------------------------------------------
    # 1. Get order
    # ---------------------------------------------------------
    order = get_order(
        db=db,
        order_id=order_id
    )

    # ---------------------------------------------------------
    # 2. Check current status
    # ---------------------------------------------------------
    current_status = order.order_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    # ---------------------------------------------------------
    # 3. Only Pending orders can be accepted
    # ---------------------------------------------------------
    if current_status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be accepted"
        )

    # ---------------------------------------------------------
    # 4. Change order status
    # ---------------------------------------------------------
    order.order_status = "Accepted"

    # ---------------------------------------------------------
    # 5. Create Accepted tracking record
    # ---------------------------------------------------------
    add_tracking_record(
        db=db,
        order_id=order.id,
        status="Accepted",
        location=None,
        remarks="Order accepted by restaurant"
    )

    # ---------------------------------------------------------
    # 6. Save changes
    # ---------------------------------------------------------
    db.commit()
    db.refresh(order)

    return order


def mark_food_ready(
    db: Session,
    order_id: int
):
    # ---------------------------------------------------------
    # 1. Get order
    # ---------------------------------------------------------
    order = get_order(
        db=db,
        order_id=order_id
    )

    # ---------------------------------------------------------
    # 2. Check current status
    # ---------------------------------------------------------
    current_status = order.order_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    # ---------------------------------------------------------
    # 3. Only Accepted orders can be marked as Ready
    # ---------------------------------------------------------
    if current_status != "Accepted":
        raise HTTPException(
            status_code=400,
            detail="Only accepted orders can be marked as food ready"
        )

    # ---------------------------------------------------------
    # 4. Change order status
    # ---------------------------------------------------------
    order.order_status = "Ready"

    # ---------------------------------------------------------
    # 5. Create Food Ready tracking record
    # ---------------------------------------------------------
    add_tracking_record(
        db=db,
        order_id=order.id,
        status="Ready",
        location=None,
        remarks="Food is ready for pickup"
    )

    # ---------------------------------------------------------
    # 6. Save changes
    # ---------------------------------------------------------
    db.commit()
    db.refresh(order)

    return order


def get_orders(
    db: Session,
    customer_id: int | None = None
):
    query = db.query(Order)

    if customer_id is not None:
        query = query.filter(
            Order.customer_id == customer_id
        )

    return (
        query
        .order_by(Order.id.desc())
        .all()
    )


def get_order(
    db: Session,
    order_id: int
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


def cancel_order(
    db: Session,
    order_id: int
):
    order = get_order(
        db=db,
        order_id=order_id
    )

    current_status = order.order_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    if current_status in [
        "Delivered",
        "Cancelled"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Order cannot be cancelled"
        )

    order.order_status = "Cancelled"

    # ---------------------------------------------------------
    # Automatically create Cancelled tracking
    # ---------------------------------------------------------
    add_tracking_record(
        db=db,
        order_id=order.id,
        status="Cancelled",
        location=None,
        remarks="Order cancelled"
    )

    db.commit()
    db.refresh(order)

    return order


def complete_delivery(
    db: Session,
    order_id: int
):
    order = get_order(
        db=db,
        order_id=order_id
    )

    current_status = order.order_status

    if hasattr(current_status, "value"):
        current_status = current_status.value

    if current_status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancelled order cannot be delivered"
        )

    if not order.delivery_partner_id:
        raise HTTPException(
            status_code=400,
            detail="No delivery partner assigned to this order"
        )

    order.order_status = "Delivered"

    partner = (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.id == order.delivery_partner_id
        )
        .first()
    )

    if partner:
        partner.availability_status = (
            DeliveryPartnerStatus.AVAILABLE
        )

    # ---------------------------------------------------------
    # Automatically create Delivered tracking
    # ---------------------------------------------------------
    add_tracking_record(
        db=db,
        order_id=order.id,
        status="Delivered",
        location=partner.current_location if partner else None,
        remarks="Order delivered successfully"
    )

    db.commit()
    db.refresh(order)

    return order


def search_orders(
    db: Session,
    status: str | None = None,
    payment_status: str | None = None,
    restaurant_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    query = db.query(Order)

    # ---------------------------------------------------------
    # Order status filter
    # ---------------------------------------------------------
    if status:
        query = query.filter(
            Order.order_status == status
        )

    # ---------------------------------------------------------
    # Payment status filter
    # ---------------------------------------------------------
    if payment_status:
        query = query.filter(
            Order.payment_status == payment_status
        )

    # ---------------------------------------------------------
    # Restaurant filter
    # ---------------------------------------------------------
    if restaurant_id is not None:
        query = query.filter(
            Order.restaurant_id == restaurant_id
        )

    # ---------------------------------------------------------
    # Start date filter
    # ---------------------------------------------------------
    if start_date:
        start_datetime = datetime.fromisoformat(
            start_date
        )

        query = query.filter(
            Order.created_at >= start_datetime
        )

    # ---------------------------------------------------------
    # End date filter
    # ---------------------------------------------------------
    if end_date:
        end_datetime = datetime.fromisoformat(
            end_date
        )

        query = query.filter(
            Order.created_at <= end_datetime
        )

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------
    sort_columns = {
        "id": Order.id,
        "created_at": Order.created_at,
        "total_amount": Order.total_amount,
        "order_status": Order.order_status,
    }

    sort_column = sort_columns.get(
        sort_by,
        Order.id
    )

    if sort_order.lower() == "asc":
        query = query.order_by(
            sort_column.asc()
        )
    else:
        query = query.order_by(
            sort_column.desc()
        )

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------
    offset = (page - 1) * limit

    return (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )