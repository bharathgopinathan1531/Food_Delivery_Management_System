from sqlalchemy.orm import Session

from app.models.customer import Customer, Address
from app.schemas.customer import CustomerCreate, AddressCreate, AddressUpdate


def create_customer(
    db: Session,
    customer_data: CustomerCreate
):
    customer = Customer(
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer(
    db: Session,
    customer_id: int
):
    return (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )


def create_address(
    db: Session,
    customer_id: int,
    address_data: AddressCreate
):
    if address_data.is_default:
        (
            db.query(Address)
            .filter(
                Address.customer_id == customer_id,
                Address.is_default.is_(True)
            )
            .update(
                {"is_default": False},
                synchronize_session=False
            )
        )

    address = Address(
        customer_id=customer_id,
        address_line=address_data.address_line,
        city=address_data.city,
        pincode=address_data.pincode,
        latitude=address_data.latitude,
        longitude=address_data.longitude,
        address_type=address_data.address_type,
        is_default=address_data.is_default,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


def get_customer_addresses(
    db: Session,
    customer_id: int
):
    return (
        db.query(Address)
        .filter(Address.customer_id == customer_id)
        .all()
    )


def get_address(
    db: Session,
    address_id: int
):
    return (
        db.query(Address)
        .filter(Address.id == address_id)
        .first()
    )


def update_address(
    db: Session,
    address: Address,
    address_data: AddressUpdate
):
    update_data = address_data.model_dump(
        exclude_unset=True
    )

    if update_data.get("is_default") is True:
        (
            db.query(Address)
            .filter(
                Address.customer_id == address.customer_id,
                Address.id != address.id,
                Address.is_default.is_(True)
            )
            .update(
                {"is_default": False},
                synchronize_session=False
            )
        )

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)

    return address