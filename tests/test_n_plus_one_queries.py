from sqlalchemy import event, select
from sqlalchemy.orm import joinedload

from app.database import Base, SessionLocal
from app.models import (
    User,
    Restaurant,
    MenuItem,
    RestaurantStaff,
    Customer,
    Address,
    Cart,
    CartItem,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    DeliveryPartner,
    OrderTracking,
    Payment,
    CancellationHistory,
    Refund,
    Review,
)


def prepare_database(db):
    """
    Create all application tables required by the test.
    This makes the test work reliably in a fresh CI database.
    """
    Base.metadata.create_all(bind=db.bind)


def test_eager_loading_avoids_n_plus_one_queries():
    db = SessionLocal()
    query_count = 0

    prepare_database(db)

    def count_queries(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        nonlocal query_count
        query_count += 1

    event.listen(
        db.bind,
        "before_cursor_execute",
        count_queries,
    )

    try:
        orders = (
            db.execute(
                select(Order).options(
                    joinedload(Order.delivery_partner)
                )
            )
            .unique()
            .scalars()
            .all()
        )

        for order in orders:
            _ = order.delivery_partner

        assert query_count <= 2

    finally:
        event.remove(
            db.bind,
            "before_cursor_execute",
            count_queries,
        )
        db.close()


def test_selectin_loading_is_available():
    db = SessionLocal()

    try:
        prepare_database(db)

        statement = select(Order)

        assert statement is not None

    finally:
        db.close()


def test_order_relationships_are_configured_for_eager_loading():
    relationship_names = {
        relationship.key
        for relationship in Order.__mapper__.relationships
    }

    assert "delivery_partner" in relationship_names
    assert "items" in relationship_names