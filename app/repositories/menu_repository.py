from sqlalchemy.orm import Session

from app.models.menu import MenuItem


def create(db: Session, menu_item: MenuItem):
    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)
    return menu_item


def get_all(db: Session):
    return (
        db.query(MenuItem)
        .order_by(MenuItem.id.desc())
        .all()
    )


def get_by_id(db: Session, menu_item_id: int):
    return (
        db.query(MenuItem)
        .filter(MenuItem.id == menu_item_id)
        .first()
    )


def get_by_restaurant(db: Session, restaurant_id: int):
    return (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == restaurant_id)
        .order_by(MenuItem.id.desc())
        .all()
    )


def search_menu_items(
    db: Session,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    vegetarian: bool | None = None,
    spicy_level: str | None = None,
    availability: bool | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc"
):
    query = db.query(MenuItem)

    # Category filter
    if category:
        query = query.filter(
            MenuItem.category.ilike(
                f"%{category}%"
            )
        )

    # Minimum price
    if min_price is not None:
        query = query.filter(
            MenuItem.price >= min_price
        )

    # Maximum price
    if max_price is not None:
        query = query.filter(
            MenuItem.price <= max_price
        )

    # Vegetarian filter
    if vegetarian is not None:
        query = query.filter(
            MenuItem.vegetarian == vegetarian
        )

    # Spicy level filter
    if spicy_level:
        query = query.filter(
            MenuItem.spicy_level == spicy_level
        )

    # Availability filter
    if availability is not None:
        query = query.filter(
            MenuItem.availability == availability
        )

    # Sorting
    sort_columns = {
        "id": MenuItem.id,
        "name": MenuItem.name,
        "category": MenuItem.category,
        "price": MenuItem.price,
        "preparation_time": MenuItem.preparation_time,
    }

    sort_column = sort_columns.get(
        sort_by,
        MenuItem.id
    )

    if sort_order.lower() == "asc":
        query = query.order_by(
            sort_column.asc()
        )
    else:
        query = query.order_by(
            sort_column.desc()
        )

    # Pagination
    offset = (page - 1) * limit

    query = query.offset(offset).limit(limit)

    return query.all()


def update(db: Session, menu_item: MenuItem):
    db.commit()
    db.refresh(menu_item)
    return menu_item


def delete(db: Session, menu_item: MenuItem):
    db.delete(menu_item)
    db.commit()