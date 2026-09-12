from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer

from app.repositories.cart import (
    add_item,
    clear_cart,
    get_or_create_cart,
    remove_item,
    update_item,
)

from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


def validate_customer(
    customer_id: int,
    db: Session,
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=201,
)
def add_cart_item(
    item_data: CartItemCreate,
    customer_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    validate_customer(
        customer_id=customer_id,
        db=db,
    )

    return add_item(
        db=db,
        customer_id=customer_id,
        item_data=item_data,
    )


@router.get(
    "",
    response_model=CartResponse,
)
def get_customer_cart(
    customer_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    validate_customer(
        customer_id=customer_id,
        db=db,
    )

    return get_or_create_cart(
        db=db,
        customer_id=customer_id,
    )


@router.put(
    "/items/{item_id}",
    response_model=CartResponse,
)
def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    customer_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    validate_customer(
        customer_id=customer_id,
        db=db,
    )

    return update_item(
        db=db,
        customer_id=customer_id,
        item_id=item_id,
        item_data=item_data,
    )


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
)
def delete_cart_item(
    item_id: int,
    customer_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    validate_customer(
        customer_id=customer_id,
        db=db,
    )

    return remove_item(
        db=db,
        customer_id=customer_id,
        item_id=item_id,
    )


@router.delete(
    "/clear",
    response_model=CartResponse,
)
def clear_customer_cart(
    customer_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    validate_customer(
        customer_id=customer_id,
        db=db,
    )

    return clear_cart(
        db=db,
        customer_id=customer_id,
    )