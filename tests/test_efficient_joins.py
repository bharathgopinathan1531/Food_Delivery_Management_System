from sqlalchemy import select

from app.database import SessionLocal
from app.models.order import Order
from app.models.customer import Customer
from app.models.restaurant import Restaurant
from app.models.delivery_partner import DeliveryPartner


def test_order_customer_restaurant_join():
    """
    Verify that orders can be efficiently joined with
    customers and restaurants using SQL JOINs.
    """

    db = SessionLocal()

    try:
        statement = (
            select(
                Order,
                Customer,
                Restaurant
            )
            .join(
                Customer,
                Order.customer_id == Customer.id
            )
            .join(
                Restaurant,
                Order.restaurant_id == Restaurant.id
            )
        )

        results = db.execute(statement).all()

        assert results is not None

    finally:
        db.close()


def test_order_delivery_partner_join():
    """
    Verify that orders can be joined with delivery partners
    using a LEFT OUTER JOIN because delivery_partner_id
    can be NULL.
    """

    db = SessionLocal()

    try:
        statement = (
            select(
                Order,
                DeliveryPartner
            )
            .outerjoin(
                DeliveryPartner,
                Order.delivery_partner_id
                == DeliveryPartner.id
            )
        )

        results = db.execute(statement).all()

        assert results is not None

    finally:
        db.close()


def test_join_query_uses_sql_join():
    """
    Verify that SQLAlchemy generates JOIN SQL instead of
    loading related records separately.
    """

    statement = (
        select(
            Order,
            Customer,
            Restaurant
        )
        .join(
            Customer,
            Order.customer_id == Customer.id
        )
        .join(
            Restaurant,
            Order.restaurant_id == Restaurant.id
        )
    )

    sql = str(
        statement.compile(
            compile_kwargs={
                "literal_binds": True
            }
        )
    ).upper()

    assert "JOIN" in sql
    assert "CUSTOMERS" in sql
    assert "RESTAURANTS" in sql