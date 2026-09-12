from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.order import Order


def create_review(db: Session, review_data):
    # Check order exists
    order = (
        db.query(Order)
        .filter(Order.id == review_data.order_id)
        .first()
    )

    if not order:
        raise ValueError("Order not found")

    # Only delivered orders can be reviewed
    if order.order_status != "Delivered":
        raise ValueError(
            "Only delivered orders can be reviewed"
        )

    # Customer must own the order
    if order.customer_id != review_data.customer_id:
        raise ValueError(
            "Customer is not authorized to review this order"
        )

    # Restaurant must match the order
    if order.restaurant_id != review_data.restaurant_id:
        raise ValueError(
            "Restaurant does not belong to this order"
        )

    # Prevent duplicate food-item review
    if review_data.food_item_id is not None:
        existing_food_review = (
            db.query(Review)
            .filter(
                Review.order_id == review_data.order_id,
                Review.food_item_id == review_data.food_item_id,
            )
            .first()
        )

        if existing_food_review:
            raise ValueError(
                "You have already reviewed this food item for this order"
            )

    # Prevent duplicate restaurant-only review
    if (
        review_data.food_item_id is None
        and review_data.delivery_partner_id is None
    ):
        existing_restaurant_review = (
            db.query(Review)
            .filter(
                Review.order_id == review_data.order_id,
                Review.restaurant_id == review_data.restaurant_id,
                Review.food_item_id.is_(None),
                Review.delivery_partner_id.is_(None),
            )
            .first()
        )

        if existing_restaurant_review:
            raise ValueError(
                "You have already reviewed this restaurant for this order"
            )

    # Prevent duplicate delivery-partner review
    if review_data.delivery_partner_id is not None:
        existing_partner_review = (
            db.query(Review)
            .filter(
                Review.order_id == review_data.order_id,
                Review.delivery_partner_id
                == review_data.delivery_partner_id,
            )
            .first()
        )

        if existing_partner_review:
            raise ValueError(
                "You have already reviewed this delivery partner for this order"
            )

    review = Review(
        customer_id=review_data.customer_id,
        order_id=review_data.order_id,
        restaurant_id=review_data.restaurant_id,
        food_item_id=review_data.food_item_id,
        delivery_partner_id=review_data.delivery_partner_id,
        rating=review_data.rating,
        review=review_data.review,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


def get_restaurant_reviews(
    db: Session,
    restaurant_id: int
):
    return (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )


def get_food_item_reviews(
    db: Session,
    food_item_id: int
):
    return (
        db.query(Review)
        .filter(Review.food_item_id == food_item_id)
        .order_by(Review.created_at.desc())
        .all()
    )