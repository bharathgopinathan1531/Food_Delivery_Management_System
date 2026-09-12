from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

from app.models.user import User
from app.models.customer import Customer, Address
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.review import Review
from app.models.menu import MenuItem, SpicyLevel
from app.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerStatus,
)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False
        },
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_user(
    db,
    name="Test User",
    email="user@example.com",
    phone="9876543210",
    role="Customer",
):
    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash="hashed-password",
        role=role,
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def customer(db):
    user = create_user(
        db,
        name="Customer User",
        email="customer@example.com",
        phone="9000000001",
        role="Customer",
    )

    customer = Customer(
        user_id=user.id,
        name="Bharath",
        email="bharath@example.com",
        phone="9000000011",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@pytest.fixture()
def second_customer(db):
    user = create_user(
        db,
        name="Second Customer",
        email="customer2@example.com",
        phone="9000000002",
        role="Customer",
    )

    customer = Customer(
        user_id=user.id,
        name="Second Customer",
        email="secondcustomer@example.com",
        phone="9000000012",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@pytest.fixture()
def address(db, customer):
    address = Address(
        customer_id=customer.id,
        address_line="12 Main Street",
        city="Chennai",
        pincode="600001",
        latitude=13.0827,
        longitude=80.2707,
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


@pytest.fixture()
def restaurant(db):
    owner = create_user(
        db,
        name="Restaurant Owner",
        email="owner@example.com",
        phone="9000000003",
        role="Restaurant Owner",
    )

    restaurant = Restaurant(
        restaurant_name="Test Restaurant",
        owner_id=owner.id,
        address="100 Food Street",
        city="Chennai",
        phone="9000000004",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


@pytest.fixture()
def menu_item(db, restaurant):
    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Test Food",
        description="Test food item",
        price=250.0,
        preparation_time=20,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@pytest.fixture()
def second_menu_item(db, restaurant):
    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Second Test Food",
        description="Second test food item",
        price=300.0,
        preparation_time=25,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MEDIUM,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@pytest.fixture()
def delivery_partner(db):
    partner = DeliveryPartner(
        name="Test Delivery Partner",
        phone="9000000099",
        vehicle_type="Bike",
        vehicle_number="TN99AB9999",
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    return partner


@pytest.fixture()
def second_delivery_partner(db):
    partner = DeliveryPartner(
        name="Second Delivery Partner",
        phone="9000000098",
        vehicle_type="Bike",
        vehicle_number="TN99AB9998",
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    return partner


def create_order(
    db,
    customer,
    restaurant,
    address,
    status=OrderStatus.DELIVERED,
):
    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=0.0,
        total_amount=520.0,
        order_status=status,
        payment_status=PaymentStatus.PAID,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@pytest.fixture()
def delivered_order(
    db,
    customer,
    restaurant,
    address,
):
    return create_order(
        db,
        customer,
        restaurant,
        address,
    )


@pytest.fixture()
def pending_order(
    db,
    customer,
    restaurant,
    address,
):
    return create_order(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.PENDING,
    )


def review_payload(
    customer_id,
    order_id,
    restaurant_id,
    rating=5,
    review="Excellent food and service",
    food_item_id=None,
    delivery_partner_id=None,
):
    payload = {
        "customer_id": customer_id,
        "order_id": order_id,
        "restaurant_id": restaurant_id,
        "rating": rating,
        "review": review,
    }

    if food_item_id is not None:
        payload["food_item_id"] = food_item_id

    if delivery_partner_id is not None:
        payload["delivery_partner_id"] = delivery_partner_id

    return payload


def test_create_restaurant_review(
    client,
    delivered_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer.id
    assert data["order_id"] == delivered_order.id
    assert data["restaurant_id"] == restaurant.id
    assert data["food_item_id"] is None
    assert data["delivery_partner_id"] is None
    assert data["rating"] == 5
    assert data["review"] == "Excellent food and service"
    assert data["created_at"] is not None


def test_create_review_without_review_text(
    client,
    delivered_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            review=None,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["rating"] == 5
    assert data["review"] is None


def test_create_food_item_review(
    client,
    delivered_order,
    customer,
    restaurant,
    menu_item,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=4,
            review="Good food",
            food_item_id=menu_item.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["food_item_id"] == menu_item.id
    assert data["delivery_partner_id"] is None
    assert data["rating"] == 4


def test_create_delivery_partner_review(
    client,
    delivered_order,
    customer,
    restaurant,
    delivery_partner,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=4,
            review="Fast delivery",
            delivery_partner_id=delivery_partner.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["delivery_partner_id"] == delivery_partner.id
    assert data["food_item_id"] is None
    assert data["rating"] == 4


def test_create_review_order_not_found(
    client,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            9999,
            restaurant.id,
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Order not found"


def test_create_review_only_delivered_orders_allowed(
    client,
    pending_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            pending_order.id,
            restaurant.id,
        ),
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Only delivered orders can be reviewed"
    )


def test_create_review_customer_must_own_order(
    client,
    delivered_order,
    second_customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            second_customer.id,
            delivered_order.id,
            restaurant.id,
        ),
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Customer is not authorized to review this order"
    )


def test_create_review_restaurant_must_match_order(
    client,
    delivered_order,
    customer,
    db,
):
    second_owner = create_user(
        db,
        name="Second Owner",
        email="owner2@example.com",
        phone="9000000005",
        role="Restaurant Owner",
    )

    second_restaurant = Restaurant(
        restaurant_name="Second Restaurant",
        owner_id=second_owner.id,
        address="200 Food Street",
        city="Chennai",
        phone="9000000006",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(second_restaurant)
    db.commit()
    db.refresh(second_restaurant)

    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            second_restaurant.id,
        ),
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Restaurant does not belong to this order"
    )


def test_duplicate_restaurant_review_rejected(
    client,
    delivered_order,
    customer,
    restaurant,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            review="First review",
        ),
    )

    assert first.status_code == 201

    second = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            review="Second review",
        ),
    )

    assert second.status_code == 400

    assert (
        second.json()["detail"]
        == "You have already reviewed this restaurant for this order"
    )


def test_duplicate_food_item_review_rejected(
    client,
    delivered_order,
    customer,
    restaurant,
    menu_item,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            food_item_id=menu_item.id,
            review="First food review",
        ),
    )

    assert first.status_code == 201

    second = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            food_item_id=menu_item.id,
            review="Second food review",
        ),
    )

    assert second.status_code == 400

    assert (
        second.json()["detail"]
        == "You have already reviewed this food item for this order"
    )


def test_same_order_can_review_different_food_items(
    client,
    delivered_order,
    customer,
    restaurant,
    menu_item,
    second_menu_item,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            food_item_id=menu_item.id,
            review="Food item one",
        ),
    )

    second = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            food_item_id=second_menu_item.id,
            review="Food item two",
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["food_item_id"] == menu_item.id
    assert second.json()["food_item_id"] == second_menu_item.id


def test_duplicate_delivery_partner_review_rejected(
    client,
    delivered_order,
    customer,
    restaurant,
    delivery_partner,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            delivery_partner_id=delivery_partner.id,
            review="Fast delivery",
        ),
    )

    assert first.status_code == 201

    second = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            delivery_partner_id=delivery_partner.id,
            review="Another delivery review",
        ),
    )

    assert second.status_code == 400

    assert (
        second.json()["detail"]
        == "You have already reviewed this delivery partner for this order"
    )


def test_same_order_can_review_different_delivery_partners(
    client,
    delivered_order,
    customer,
    restaurant,
    delivery_partner,
    second_delivery_partner,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            delivery_partner_id=delivery_partner.id,
        ),
    )

    second = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            delivery_partner_id=second_delivery_partner.id,
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201


def test_rating_below_one_rejected(
    client,
    delivered_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=0,
        ),
    )

    assert response.status_code == 422


def test_rating_above_five_rejected(
    client,
    delivered_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=6,
        ),
    )

    assert response.status_code == 422


def test_review_text_over_1000_characters_rejected(
    client,
    delivered_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            review="x" * 1001,
        ),
    )

    assert response.status_code == 422


def test_review_text_exactly_1000_characters_allowed(
    client,
    delivered_order,
    customer,
    restaurant,
):
    review_text = "x" * 1000

    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            review=review_text,
        ),
    )

    assert response.status_code == 201

    assert response.json()["review"] == review_text


def test_get_restaurant_reviews(
    client,
    delivered_order,
    customer,
    restaurant,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=5,
            review="Excellent",
        ),
    )

    assert first.status_code == 201

    response = client.get(
        f"/reviews/restaurants/{restaurant.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_id"] == restaurant.id
    assert data[0]["rating"] == 5
    assert data[0]["review"] == "Excellent"


def test_get_restaurant_reviews_empty(
    client,
    restaurant,
):
    response = client.get(
        f"/reviews/restaurants/{restaurant.id}"
    )

    assert response.status_code == 200

    assert response.json() == []


def test_get_food_item_reviews(
    client,
    delivered_order,
    customer,
    restaurant,
    menu_item,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=4,
            review="Tasty food",
            food_item_id=menu_item.id,
        ),
    )

    assert first.status_code == 201

    response = client.get(
        f"/reviews/food-items/{menu_item.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["food_item_id"] == menu_item.id
    assert data[0]["rating"] == 4
    assert data[0]["review"] == "Tasty food"


def test_get_food_item_reviews_empty(
    client,
):
    response = client.get(
        "/reviews/food-items/9999"
    )

    assert response.status_code == 200

    assert response.json() == []


def test_multiple_reviews_are_saved(
    client,
    db,
    delivered_order,
    customer,
    restaurant,
    menu_item,
    second_menu_item,
):
    first = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            food_item_id=menu_item.id,
            rating=5,
            review="Excellent",
        ),
    )

    second = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            food_item_id=second_menu_item.id,
            rating=4,
            review="Very good",
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    reviews = (
        db.query(Review)
        .filter(
            Review.order_id == delivered_order.id
        )
        .all()
    )

    assert len(reviews) == 2


def test_created_review_persists_in_database(
    client,
    db,
    delivered_order,
    customer,
    restaurant,
):
    response = client.post(
        "/reviews",
        json=review_payload(
            customer.id,
            delivered_order.id,
            restaurant.id,
            rating=3,
            review="Average experience",
        ),
    )

    assert response.status_code == 201

    review_id = response.json()["id"]

    saved_review = (
        db.query(Review)
        .filter(
            Review.id == review_id
        )
        .first()
    )

    assert saved_review is not None
    assert saved_review.customer_id == customer.id
    assert saved_review.order_id == delivered_order.id
    assert saved_review.restaurant_id == restaurant.id
    assert saved_review.rating == 3
    assert saved_review.review == "Average experience"