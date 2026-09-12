from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.models.review import Review


def create(
    db: Session,
    restaurant: Restaurant
):
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


def get_all(
    db: Session
):
    return (
        db.query(Restaurant)
        .filter(
            Restaurant.status != None,
            Restaurant.is_deleted == False
        )
        .order_by(Restaurant.id.desc())
        .all()
    )


def get_by_id(
    db: Session,
    restaurant_id: int
):
    return (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id,
            Restaurant.is_deleted == False
        )
        .first()
    )


def search_restaurants(
    db: Session,
    cuisine: str | None = None,
    city: str | None = None,
    rating: float | None = None,
    status: str | None = None,
    delivery_time: int | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc"
):
    average_rating = func.coalesce(
        func.avg(Review.rating),
        0
    )

    query = (
        db.query(Restaurant)
        .outerjoin(
            Review,
            Review.restaurant_id == Restaurant.id
        )
        .filter(
            Restaurant.is_deleted == False
        )
        .group_by(Restaurant.id)
    )

    # ---------------------------------------------------------
    # Cuisine filter
    # ---------------------------------------------------------
    if cuisine:
        query = query.filter(
            Restaurant.cuisine_type.ilike(
                f"%{cuisine}%"
            )
        )

    # ---------------------------------------------------------
    # City filter
    # ---------------------------------------------------------
    if city:
        query = query.filter(
            Restaurant.city.ilike(
                f"%{city}%"
            )
        )

    # ---------------------------------------------------------
    # Status filter
    # ---------------------------------------------------------
    if status:
        query = query.filter(
            Restaurant.status == status
        )

    # ---------------------------------------------------------
    # Rating filter
    # ---------------------------------------------------------
    if rating is not None:
        query = query.having(
            average_rating >= rating
        )

    # ---------------------------------------------------------
    # Delivery time filter
    # ---------------------------------------------------------
    if delivery_time is not None:
        query = query.filter(
            Restaurant.delivery_time <= delivery_time
        )

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------
    sort_columns = {
        "id": Restaurant.id,
        "name": Restaurant.restaurant_name,
        "city": Restaurant.city,
        "cuisine": Restaurant.cuisine_type,
        "rating": average_rating,
        "delivery_time": Restaurant.delivery_time,
    }

    sort_column = sort_columns.get(
        sort_by,
        Restaurant.id
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


def update(
    db: Session,
    restaurant: Restaurant
):
    db.commit()
    db.refresh(restaurant)

    return restaurant


def delete(
    db: Session,
    restaurant: Restaurant
):
    restaurant.is_deleted = True

    db.commit()
    db.refresh(restaurant)

    return restaurant