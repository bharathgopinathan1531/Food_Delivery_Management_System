from fastapi import (
    APIRouter,
    Depends,
    Query,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from app.services.notification_service import (
    notify_order_placed,
    notify_order_accepted,
    notify_food_ready,
    notify_driver_assigned,
    notify_out_for_delivery,
    notify_order_delivered,
)

from app.database import get_db

from app.repositories.order import (
    accept_order,
    complete_delivery,
    create_order,
    get_order,
    get_orders,
    mark_food_ready,
    search_orders,
)

from app.repositories.cancellation import (
    cancel_order,
)

from app.repositories.delivery_partner import (
    assign_driver_to_order,
)

from app.repositories.payment import (
    get_order_payment,
)

from app.schemas.order import (
    OrderCreate,
    OrderResponse,
)

from app.schemas.cancellation import (
    CancellationRequest,
)

from app.schemas.payment import (
    PaymentResponse,
)

from app.schemas.search import (
    OrderSearchParams,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


# ============================================================
# CREATE ORDER
# ============================================================

@router.post(
    "",
    response_model=OrderResponse,
    status_code=201
)
def create_order_api(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    order = create_order(
        db=db,
        order_data=order_data,
    )

    background_tasks.add_task(
        notify_order_placed,
        order.customer_id,
        order.id,
    )

    return order


# ============================================================
# ACCEPT ORDER
# ============================================================

@router.post(
    "/{order_id}/accept",
    response_model=OrderResponse
)
def accept_order_api(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    order = accept_order(
        db=db,
        order_id=order_id,
    )

    background_tasks.add_task(
        notify_order_accepted,
        order.customer_id,
        order.id,
    )

    return order


# ============================================================
# FOOD READY
# ============================================================

@router.post(
    "/{order_id}/food-ready",
    response_model=OrderResponse
)
def mark_food_ready_api(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    order = mark_food_ready(
        db=db,
        order_id=order_id,
    )

    background_tasks.add_task(
        notify_food_ready,
        order.customer_id,
        order.id,
    )

    return order


# ============================================================
# GET ORDERS
# ============================================================

@router.get(
    "",
    response_model=list[OrderResponse]
)
def get_orders_api(
    customer_id: int | None = Query(
        default=None,
        gt=0
    ),
    db: Session = Depends(get_db),
):
    return get_orders(
        db=db,
        customer_id=customer_id,
    )


# ============================================================
# SEARCH ORDERS
# ============================================================

@router.get(
    "/search",
    response_model=list[OrderResponse]
)
def search_orders_api(
    params: OrderSearchParams = Depends(),
    db: Session = Depends(get_db),
):
    return search_orders(
        db=db,
        status=params.status,
        payment_status=params.payment_status,
        restaurant_id=params.restaurant_id,
        start_date=params.start_date,
        end_date=params.end_date,
        page=params.page,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order.value,
    )


# ============================================================
# GET SINGLE ORDER
# ============================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order_api(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_order(
        db=db,
        order_id=order_id,
    )


# ============================================================
# CANCEL ORDER
# ============================================================

@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse
)
def cancel_order_api(
    order_id: int,
    cancel_data: CancellationRequest,
    db: Session = Depends(get_db),
):
    return cancel_order(
        db=db,
        order_id=order_id,
        cancellation_data=cancel_data,
    )


# ============================================================
# ASSIGN DRIVER
# ============================================================

@router.post(
    "/{order_id}/assign-driver",
    response_model=OrderResponse
)
def assign_driver_api(
    order_id: int,
    partner_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    order = assign_driver_to_order(
        db=db,
        order_id=order_id,
        partner_id=partner_id,
    )

    background_tasks.add_task(
        notify_driver_assigned,
        order.customer_id,
        order.id,
    )

    background_tasks.add_task(
        notify_out_for_delivery,
        order.customer_id,
        order.id,
    )

    return order


# ============================================================
# COMPLETE DELIVERY
# ============================================================

@router.post(
    "/{order_id}/deliver",
    response_model=OrderResponse
)
def complete_delivery_api(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    order = complete_delivery(
        db=db,
        order_id=order_id,
    )

    background_tasks.add_task(
        notify_order_delivered,
        order.customer_id,
        order.id,
    )

    return order


# ============================================================
# GET ORDER PAYMENT
# ============================================================

@router.get(
    "/{order_id}/payment",
    response_model=PaymentResponse,
)
def get_order_payment_api(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_order_payment(
        db=db,
        order_id=order_id,
    )