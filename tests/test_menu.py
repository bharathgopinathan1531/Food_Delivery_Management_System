from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.menu import MenuItem, SpicyLevel
from app.models.restaurant_staff import RestaurantStaff

from app.utils.dependencies import get_current_user


# ============================================================
# DATABASE FIXTURE
# ============================================================

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
        autocommit=False
    )

    Base.metadata.create_all(
        bind=engine
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        Base.metadata.drop_all(
            bind=engine
        )

        engine.dispose()


# ============================================================
# CLIENT FIXTURE
# ============================================================

@pytest.fixture()
def client(db):

    def override_get_db():
        yield db

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================
# USER HELPER
# ============================================================

def create_user(
    db,
    role,
    email
):
    user = User(
        name=role,
        email=email,
        phone="9876543210",
        password_hash="hashed-password",
        role=role,
        is_active=True,
        is_deleted=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# USER FIXTURES
# ============================================================

@pytest.fixture()
def admin(db):
    return create_user(
        db,
        "Admin",
        "admin@example.com"
    )


@pytest.fixture()
def owner(db):
    return create_user(
        db,
        "Restaurant Owner",
        "owner@example.com"
    )


@pytest.fixture()
def other_owner(db):
    return create_user(
        db,
        "Restaurant Owner",
        "otherowner@example.com"
    )


@pytest.fixture()
def staff(db):
    return create_user(
        db,
        "Restaurant Staff",
        "staff@example.com"
    )


@pytest.fixture()
def unassigned_staff(db):
    return create_user(
        db,
        "Restaurant Staff",
        "unassigned@example.com"
    )


@pytest.fixture()
def customer_user(db):
    return create_user(
        db,
        "Customer",
        "customer@example.com"
    )


# ============================================================
# RESTAURANT HELPER
# ============================================================

def create_restaurant(
    db,
    owner_id,
    name="Test Restaurant",
    phone="9000000001"
):

    restaurant = Restaurant(
        restaurant_name=name,
        owner_id=owner_id,
        address="123 Main Street",
        city="Chennai",
        phone=phone,
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10.0,
        delivery_time=30
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


# ============================================================
# RESTAURANT FIXTURES
# ============================================================

@pytest.fixture()
def restaurant(
    db,
    owner
):
    return create_restaurant(
        db,
        owner.id
    )


@pytest.fixture()
def other_restaurant(
    db,
    other_owner
):
    return create_restaurant(
        db,
        other_owner.id,
        name="Other Restaurant",
        phone="9000000002"
    )


# ============================================================
# AUTH HELPER
# ============================================================

def authenticate(user):

    app.dependency_overrides[
        get_current_user
    ] = lambda: user


# ============================================================
# MENU PAYLOAD
# ============================================================

def menu_payload(
    restaurant_id,
    **overrides
):

    data = {
        "restaurant_id": restaurant_id,
        "category": "Main Course",
        "name": "Chicken Biryani",
        "description": "Spicy chicken biryani",
        "price": 250.0,
        "preparation_time": 25,
        "availability": True,
        "vegetarian": False,
        "spicy_level": "Medium"
    }

    data.update(overrides)

    return data


# ============================================================
# CREATE MENU ITEM
# ============================================================

def test_create_menu_item(
    client,
    admin,
    restaurant
):

    authenticate(admin)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id
        )
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == restaurant.id
    assert data["name"] == "Chicken Biryani"
    assert data["category"] == "Main Course"
    assert data["price"] == 250.0
    assert data["preparation_time"] == 25
    assert data["availability"] is True
    assert data["vegetarian"] is False
    assert data["spicy_level"] == "Medium"


# ============================================================
# CREATE WITH DEFAULT VALUES
# ============================================================

def test_create_menu_item_with_defaults(
    client,
    admin,
    restaurant
):

    authenticate(admin)

    data = menu_payload(
        restaurant.id
    )

    data.pop("availability")
    data.pop("vegetarian")
    data.pop("spicy_level")

    response = client.post(
        "/menu/items",
        json=data
    )

    assert response.status_code == 201

    result = response.json()

    assert result["availability"] is True
    assert result["vegetarian"] is False
    assert result["spicy_level"] == "Mild"


# ============================================================
# CREATE - RESTAURANT NOT FOUND
# ============================================================

def test_create_menu_item_restaurant_not_found(
    client,
    admin
):

    authenticate(admin)

    response = client.post(
        "/menu/items",
        json=menu_payload(9999)
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Restaurant not found"
    )


# ============================================================
# OWNER CAN CREATE FOR OWN RESTAURANT
# ============================================================

def test_owner_can_create_menu_item(
    client,
    owner,
    restaurant
):

    authenticate(owner)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id
        )
    )

    assert response.status_code == 201


# ============================================================
# OWNER CANNOT CREATE FOR OTHER RESTAURANT
# ============================================================

def test_owner_cannot_create_for_other_restaurant(
    client,
    owner,
    other_restaurant
):

    authenticate(owner)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            other_restaurant.id
        )
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You can manage only your own restaurant's menu"
    )


# ============================================================
# STAFF ASSIGNED TO RESTAURANT
# ============================================================

def test_staff_can_create_for_assigned_restaurant(
    client,
    db,
    staff,
    restaurant
):

    assignment = RestaurantStaff(
        restaurant_id=restaurant.id,
        user_id=staff.id
    )

    db.add(assignment)
    db.commit()

    authenticate(staff)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id
        )
    )

    assert response.status_code == 201


# ============================================================
# STAFF NOT ASSIGNED
# ============================================================

def test_staff_cannot_create_for_unassigned_restaurant(
    client,
    unassigned_staff,
    restaurant
):

    authenticate(unassigned_staff)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id
        )
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You can manage only your assigned restaurant's menu"
    )


# ============================================================
# CUSTOMER CANNOT CREATE
# ============================================================

def test_customer_cannot_create_menu_item(
    client,
    customer_user,
    restaurant
):

    authenticate(customer_user)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id
        )
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Insufficient permissions"
    )


# ============================================================
# CREATE VALIDATION - NAME
# ============================================================

def test_create_menu_item_invalid_name(
    client,
    admin,
    restaurant
):

    authenticate(admin)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id,
            name="A"
        )
    )

    assert response.status_code == 422


# ============================================================
# CREATE VALIDATION - PRICE
# ============================================================

def test_create_menu_item_invalid_price(
    client,
    admin,
    restaurant
):

    authenticate(admin)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id,
            price=0
        )
    )

    assert response.status_code == 422


# ============================================================
# CREATE VALIDATION - PREPARATION TIME
# ============================================================

def test_create_menu_item_invalid_preparation_time(
    client,
    admin,
    restaurant
):

    authenticate(admin)

    response = client.post(
        "/menu/items",
        json=menu_payload(
            restaurant.id,
            preparation_time=0
        )
    )

    assert response.status_code == 422


# ============================================================
# GET ALL MENU ITEMS
# ============================================================

def test_get_all_menu_items(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    item1 = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Item 1",
        description="First item",
        price=100,
        preparation_time=15,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD
    )

    item2 = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Item 2",
        description="Second item",
        price=200,
        preparation_time=20,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MEDIUM
    )

    db.add_all(
        [
            item1,
            item2
        ]
    )

    db.commit()

    response = client.get(
        "/menu/items"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    # Repository sorts ID descending
    assert data[0]["name"] == "Item 2"
    assert data[1]["name"] == "Item 1"


# ============================================================
# GET BY RESTAURANT
# ============================================================

def test_get_menu_items_by_restaurant(
    client,
    admin,
    restaurant,
    other_restaurant,
    db
):

    authenticate(admin)

    item1 = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Restaurant Item",
        description="Item",
        price=200,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD
    )

    item2 = MenuItem(
        restaurant_id=other_restaurant.id,
        category="Dessert",
        name="Other Item",
        description="Other",
        price=150,
        preparation_time=10,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MILD
    )

    db.add_all(
        [
            item1,
            item2
        ]
    )

    db.commit()

    response = client.get(
        f"/menu/items?restaurant_id={restaurant.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Restaurant Item"


# ============================================================
# GET MENU ITEM BY ID
# ============================================================

def test_get_menu_item_by_id(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Biryani",
        price=250,
        preparation_time=25,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.get(
        f"/menu/items/{item.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == item.id
    assert data["name"] == "Chicken Biryani"


# ============================================================
# GET MENU ITEM NOT FOUND
# ============================================================

def test_get_menu_item_not_found(
    client,
    admin
):

    authenticate(admin)

    response = client.get(
        "/menu/items/9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Menu item not found"
    )


# ============================================================
# UPDATE MENU ITEM
# ============================================================

def test_update_menu_item(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Biryani",
        price=250,
        preparation_time=25,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.put(
        f"/menu/items/{item.id}",
        json={
            "name": "Updated Biryani",
            "price": 275,
            "availability": False
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Biryani"
    assert data["price"] == 275.0
    assert data["availability"] is False


# ============================================================
# UPDATE NOT FOUND
# ============================================================

def test_update_menu_item_not_found(
    client,
    admin
):

    authenticate(admin)

    response = client.put(
        "/menu/items/9999",
        json={
            "name": "Updated Item"
        }
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Menu item not found"
    )


# ============================================================
# OWNER CANNOT UPDATE OTHER RESTAURANT
# ============================================================

def test_owner_cannot_update_other_restaurant(
    client,
    owner,
    other_restaurant,
    db
):

    authenticate(owner)

    item = MenuItem(
        restaurant_id=other_restaurant.id,
        category="Main Course",
        name="Other Item",
        description="Item",
        price=200,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.put(
        f"/menu/items/{item.id}",
        json={
            "price": 300
        }
    )

    assert response.status_code == 403


# ============================================================
# UNASSIGNED STAFF CANNOT UPDATE
# ============================================================

def test_unassigned_staff_cannot_update(
    client,
    unassigned_staff,
    restaurant,
    db
):

    authenticate(unassigned_staff)

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Test Item",
        description="Item",
        price=200,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.put(
        f"/menu/items/{item.id}",
        json={
            "price": 300
        }
    )

    assert response.status_code == 403


# ============================================================
# DELETE MENU ITEM
# ============================================================

def test_delete_menu_item(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Delete Item",
        description="Delete me",
        price=150,
        preparation_time=15,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.delete(
        f"/menu/items/{item.id}"
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Menu item deleted successfully"
    )

    deleted_item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id == item.id
        )
        .first()
    )

    assert deleted_item is None


# ============================================================
# DELETE NOT FOUND
# ============================================================

def test_delete_menu_item_not_found(
    client,
    admin
):

    authenticate(admin)

    response = client.delete(
        "/menu/items/9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Menu item not found"
    )


# ============================================================
# CUSTOMER CANNOT DELETE
# ============================================================

def test_customer_cannot_delete_menu_item(
    client,
    customer_user,
    restaurant,
    db
):

    authenticate(customer_user)

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Protected Item",
        description="Item",
        price=200,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MILD
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.delete(
        f"/menu/items/{item.id}"
    )

    assert response.status_code == 403


# ============================================================
# SEARCH - CATEGORY
# ============================================================

def test_search_by_category(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    item1 = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Biryani",
        description="Biryani",
        price=250,
        preparation_time=25,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM
    )

    item2 = MenuItem(
        restaurant_id=restaurant.id,
        category="Dessert",
        name="Ice Cream",
        description="Ice cream",
        price=100,
        preparation_time=5,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MILD
    )

    db.add_all(
        [
            item1,
            item2
        ]
    )

    db.commit()

    response = client.get(
        "/menu/search?category=dessert"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Ice Cream"


# ============================================================
# SEARCH - PRICE RANGE
# ============================================================

def test_search_by_price_range(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    db.add_all(
        [
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Cheap",
                description="Cheap",
                price=100,
                preparation_time=10,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Middle",
                description="Middle",
                price=200,
                preparation_time=15,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Expensive",
                description="Expensive",
                price=400,
                preparation_time=30,
                availability=True,
                vegetarian=False,
                spicy_level=SpicyLevel.HOT
            )
        ]
    )

    db.commit()

    response = client.get(
        "/menu/search?min_price=150&max_price=250"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Middle"


# ============================================================
# SEARCH - VEGETARIAN
# ============================================================

def test_search_by_vegetarian(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    db.add_all(
        [
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Veg Item",
                description="Veg",
                price=150,
                preparation_time=15,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Non Veg Item",
                description="Non Veg",
                price=200,
                preparation_time=20,
                availability=True,
                vegetarian=False,
                spicy_level=SpicyLevel.MEDIUM
            )
        ]
    )

    db.commit()

    response = client.get(
        "/menu/search?vegetarian=true"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Veg Item"


# ============================================================
# SEARCH - SPICY LEVEL
# ============================================================

def test_search_by_spicy_level(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    db.add_all(
        [
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Mild Item",
                description="Mild",
                price=150,
                preparation_time=15,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Hot Item",
                description="Hot",
                price=200,
                preparation_time=20,
                availability=True,
                vegetarian=False,
                spicy_level=SpicyLevel.HOT
            )
        ]
    )

    db.commit()

    # Repository compares against SQLAlchemy enum name
    response = client.get(
        "/menu/search?spicy_level=HOT"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Hot Item"


# ============================================================
# SEARCH - AVAILABILITY
# ============================================================

def test_search_by_availability(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    db.add_all(
        [
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Available Item",
                description="Available",
                price=150,
                preparation_time=15,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Unavailable Item",
                description="Unavailable",
                price=200,
                preparation_time=20,
                availability=False,
                vegetarian=False,
                spicy_level=SpicyLevel.MEDIUM
            )
        ]
    )

    db.commit()

    response = client.get(
        "/menu/search?availability=false"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Unavailable Item"


# ============================================================
# SEARCH - PRICE SORT ASCENDING
# ============================================================

def test_search_sort_price_ascending(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    db.add_all(
        [
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="High",
                description="High",
                price=300,
                preparation_time=30,
                availability=True,
                vegetarian=False,
                spicy_level=SpicyLevel.HOT
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Low",
                description="Low",
                price=100,
                preparation_time=10,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            ),
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name="Medium",
                description="Medium",
                price=200,
                preparation_time=20,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MEDIUM
            )
        ]
    )

    db.commit()

    response = client.get(
        "/menu/search?sort_by=price&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["name"]
        for item in data
    ] == [
        "Low",
        "Medium",
        "High"
    ]


# ============================================================
# SEARCH - PAGINATION
# ============================================================

def test_search_pagination(
    client,
    admin,
    restaurant,
    db
):

    authenticate(admin)

    for index in range(5):

        db.add(
            MenuItem(
                restaurant_id=restaurant.id,
                category="Food",
                name=f"Item {index}",
                description=f"Item {index}",
                price=100 + index,
                preparation_time=10 + index,
                availability=True,
                vegetarian=True,
                spicy_level=SpicyLevel.MILD
            )
        )

    db.commit()

    response = client.get(
        "/menu/search"
        "?page=2"
        "&limit=2"
        "&sort_by=price"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert [
        item["name"]
        for item in data
    ] == [
        "Item 2",
        "Item 3"
    ]


# ============================================================
# SEARCH VALIDATION - PAGE
# ============================================================

def test_search_invalid_page(
    client,
    admin
):

    authenticate(admin)

    response = client.get(
        "/menu/search?page=0"
    )

    assert response.status_code == 422


# ============================================================
# SEARCH VALIDATION - LIMIT
# ============================================================

def test_search_invalid_limit(
    client,
    admin
):

    authenticate(admin)

    response = client.get(
        "/menu/search?limit=101"
    )

    assert response.status_code == 422