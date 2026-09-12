from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.review import ReviewCreate, ReviewResponse
from app.repositories.review import (
    create_review,
    get_restaurant_reviews,
    get_food_item_reviews,
)

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews & Ratings"]
)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED
)
def add_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_review(db, review_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/restaurants/{restaurant_id}",
    response_model=list[ReviewResponse]
)
def restaurant_reviews(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_restaurant_reviews(
        db,
        restaurant_id
    )


@router.get(
    "/food-items/{food_item_id}",
    response_model=list[ReviewResponse]
)
def food_item_reviews(
    food_item_id: int,
    db: Session = Depends(get_db)
):
    return get_food_item_reviews(
        db,
        food_item_id
    )