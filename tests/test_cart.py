from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.menu import MenuItem, SpicyLevel


# ============================================================
# TEST DATABASE
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# DATABASE OVERRIDE
# ============================================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ============================================================
# CLIENT FIXTURE
# ============================================================

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


# ============================================================
# USER FIXTURE
# ============================================================

@pytest.fixture
def user():
    db = TestingSessionLocal()

    user = User(
        name="Test User",
        email="testuser@gmail.com",
        phone="9876543210",
        password_hash="hashed_password",
        role="Customer",
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    db.close()

    return user


# ============================================================
# CUSTOMER FIXTURE
# ============================================================

@pytest.fixture
def customer(user):
    db = TestingSessionLocal()

    customer = Customer(
        user_id=user.id,
        name="Test Customer",
        email="customer@gmail.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    db.close()

    return customer


# ============================================================
# RESTAURANT FIXTURE
# ============================================================

@pytest.fixture
def restaurant(user):
    db = TestingSessionLocal()

    restaurant = Restaurant(
        restaurant_name="Test Restaurant",
        owner_id=user.id,
        address="123 Main Street",
        city="Chennai",
        phone="9876543210",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    db.close()

    return restaurant


# ============================================================
# SECOND RESTAURANT FIXTURE
# ============================================================

@pytest.fixture
def second_restaurant(user):
    db = TestingSessionLocal()

    restaurant = Restaurant(
        restaurant_name="Second Restaurant",
        owner_id=user.id,
        address="456 Second Street",
        city="Chennai",
        phone="9876543211",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    db.close()

    return restaurant


# ============================================================
# MENU ITEM FIXTURE
# ============================================================

@pytest.fixture
def menu_item(restaurant):
    db = TestingSessionLocal()

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Burger",
        description="Chicken burger",
        price=150.0,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    db.close()

    return item


# ============================================================
# SECOND MENU ITEM
# ============================================================

@pytest.fixture
def second_menu_item(restaurant):
    db = TestingSessionLocal()

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Starters",
        name="French Fries",
        description="Crispy french fries",
        price=100.0,
        preparation_time=15,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    db.close()

    return item


# ============================================================
# UNAVAILABLE MENU ITEM
# ============================================================

@pytest.fixture
def unavailable_menu_item(restaurant):
    db = TestingSessionLocal()

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Unavailable Burger",
        description="Currently unavailable burger",
        price=200.0,
        preparation_time=20,
        availability=False,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    db.close()

    return item


# ============================================================
# DIFFERENT RESTAURANT MENU ITEM
# ============================================================

@pytest.fixture
def different_restaurant_item(second_restaurant):
    db = TestingSessionLocal()

    item = MenuItem(
        restaurant_id=second_restaurant.id,
        category="Pizza",
        name="Chicken Pizza",
        description="Chicken pizza",
        price=250.0,
        preparation_time=30,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    db.close()

    return item


# ============================================================
# TEST 1
# GET CART - CREATE EMPTY CART
# ============================================================

def test_get_cart_creates_cart(client, customer):

    response = client.get(
        f"/cart?customer_id={customer.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == customer.id
    assert data["subtotal"] == 0
    assert data["items"] == []


# ============================================================
# TEST 2
# GET EXISTING CART
# ============================================================

def test_get_existing_cart(client, customer):

    first_response = client.get(
        f"/cart?customer_id={customer.id}"
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    second_response = client.get(
        f"/cart?customer_id={customer.id}"
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["id"] == first_data["id"]
    assert second_data["customer_id"] == customer.id


# ============================================================
# TEST 3
# ADD ITEM TO CART
# ============================================================

def test_add_item_to_cart(client, customer, menu_item):

    response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer.id
    assert data["restaurant_id"] == menu_item.restaurant_id
    assert data["subtotal"] == 300.0

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["menu_item_id"] == menu_item.id
    assert item["quantity"] == 2
    assert item["unit_price"] == 150.0
    assert item["subtotal"] == 300.0


# ============================================================
# TEST 4
# ADD SAME ITEM AGAIN
# ============================================================

def test_add_same_item_increases_quantity(
    client,
    customer,
    menu_item,
):

    first_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 2,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 3,
        },
    )

    assert second_response.status_code == 201

    data = second_response.json()

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["quantity"] == 5
    assert item["unit_price"] == 150.0
    assert item["subtotal"] == 750.0
    assert data["subtotal"] == 750.0


# ============================================================
# TEST 5
# NON-EXISTENT MENU ITEM
# ============================================================

def test_add_nonexistent_menu_item(client, customer):

    response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": 99999,
            "quantity": 1,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Menu item not found"


# ============================================================
# TEST 6
# UNAVAILABLE MENU ITEM
# ============================================================

def test_add_unavailable_menu_item(
    client,
    customer,
    unavailable_menu_item,
):

    response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": unavailable_menu_item.id,
            "quantity": 1,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Menu item is unavailable"
    )


# ============================================================
# TEST 7
# DIFFERENT RESTAURANT
# ============================================================

def test_cart_cannot_contain_items_from_different_restaurants(
    client,
    customer,
    menu_item,
    different_restaurant_item,
):

    first_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 1,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": different_restaurant_item.id,
            "quantity": 1,
        },
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Cart can contain items from only one restaurant"
    )


# ============================================================
# TEST 8
# ZERO QUANTITY
# ============================================================

def test_add_item_with_zero_quantity(
    client,
    customer,
    menu_item,
):

    response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 0,
        },
    )

    assert response.status_code == 422


# ============================================================
# TEST 9
# NEGATIVE QUANTITY
# ============================================================

def test_add_item_with_negative_quantity(
    client,
    customer,
    menu_item,
):

    response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": -1,
        },
    )

    assert response.status_code == 422


# ============================================================
# TEST 10
# UPDATE CART ITEM
# ============================================================

def test_update_cart_item(
    client,
    customer,
    menu_item,
):

    add_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 2,
        },
    )

    assert add_response.status_code == 201

    cart = add_response.json()

    item_id = cart["items"][0]["id"]

    update_response = client.put(
        f"/cart/items/{item_id}?customer_id={customer.id}",
        json={
            "quantity": 5,
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["quantity"] == 5
    assert item["unit_price"] == 150.0
    assert item["subtotal"] == 750.0
    assert data["subtotal"] == 750.0


# ============================================================
# TEST 11
# UPDATE NON-EXISTENT ITEM
# ============================================================

def test_update_nonexistent_cart_item(
    client,
    customer,
):

    response = client.put(
        f"/cart/items/99999?customer_id={customer.id}",
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Cart not found"


# ============================================================
# TEST 12
# REMOVE CART ITEM
# ============================================================

def test_remove_cart_item(
    client,
    customer,
    menu_item,
):

    add_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 2,
        },
    )

    assert add_response.status_code == 201

    cart = add_response.json()

    item_id = cart["items"][0]["id"]

    delete_response = client.delete(
        f"/cart/items/{item_id}?customer_id={customer.id}"
    )

    assert delete_response.status_code == 200

    data = delete_response.json()

    assert data["items"] == []
    assert data["subtotal"] == 0
    assert data["restaurant_id"] is None


# ============================================================
# TEST 13
# REMOVE NON-EXISTENT ITEM
# ============================================================

def test_remove_nonexistent_cart_item(
    client,
    customer,
):

    response = client.delete(
        f"/cart/items/99999?customer_id={customer.id}"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Cart not found"


# ============================================================
# TEST 14
# CLEAR CART
# ============================================================

def test_clear_cart(
    client,
    customer,
    menu_item,
    second_menu_item,
):

    first_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 2,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/cart/items?customer_id={customer.id}",
        json={
            "menu_item_id": second_menu_item.id,
            "quantity": 1,
        },
    )

    assert second_response.status_code == 201

    clear_response = client.delete(
        f"/cart/clear?customer_id={customer.id}"
    )

    assert clear_response.status_code == 200

    data = clear_response.json()

    assert data["items"] == []
    assert data["subtotal"] == 0
    assert data["restaurant_id"] is None


# ============================================================
# TEST 15
# INVALID CUSTOMER ID - GET CART
# ============================================================

def test_get_cart_invalid_customer(client):

    response = client.get(
        "/cart?customer_id=99999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Customer not found"


# ============================================================
# TEST 16
# INVALID CUSTOMER ID - ADD ITEM
# ============================================================

def test_add_item_invalid_customer(
    client,
    menu_item,
):

    response = client.post(
        "/cart/items?customer_id=99999",
        json={
            "menu_item_id": menu_item.id,
            "quantity": 1,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Customer not found"