from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.repositories.customer import (
    create_address,
    create_customer,
    get_address,
    get_customer,
    get_customer_addresses,
    update_address,
)
from app.schemas.customer import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    CustomerCreate,
    CustomerResponse,
)


# Customer routes
router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_customer_api(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    existing_customer = (
        db.query(Customer)
        .filter(Customer.email == customer_data.email)
        .first()
    )

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )

    return create_customer(
        db,
        customer_data
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse
)
def get_customer_api(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = get_customer(
        db,
        customer_id
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.post(
    "/{customer_id}/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED
)
def create_customer_address_api(
    customer_id: int,
    address_data: AddressCreate,
    db: Session = Depends(get_db)
):
    customer = get_customer(
        db,
        customer_id
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return create_address(
        db,
        customer_id,
        address_data
    )


@router.get(
    "/{customer_id}/addresses",
    response_model=list[AddressResponse]
)
def get_customer_addresses_api(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = get_customer(
        db,
        customer_id
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return get_customer_addresses(
        db,
        customer_id
    )


# Separate router for Address update
address_router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"]
)


@address_router.put(
    "/{address_id}",
    response_model=AddressResponse
)
def update_customer_address_api(
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db)
):
    address = get_address(
        db,
        address_id
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    return update_address(
        db,
        address,
        address_data
    )