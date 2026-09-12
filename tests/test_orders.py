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
from app.models.menu import MenuItem, SpicyLevel
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_tracking import OrderTracking
from app.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerStatus,
)
from app.models.cancellation import CancellationHistory


# ============================================================
# DATABASE
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
        autocommit=False,
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
# CLIENT
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
    name,
    email,
    role="Customer",
    phone="9876543210",
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


# ============================================================
# USER
# ============================================================

@pytest.fixture()
def user(db):
    return create_user(
        db,
        "Test User",
        "user@example.com",
    )


# ============================================================
# CUSTOMER
# ============================================================

@pytest.fixture()
def customer(db, user):

    customer = Customer(
        user_id=user.id,
        name="Bharath",
        email="customer@example.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# ============================================================
# ADDRESS
# ============================================================

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


# ============================================================
# OWNER
# ============================================================

@pytest.fixture()
def owner(db):

    return create_user(
        db,
        "Restaurant Owner",
        "owner@example.com",
        role="Restaurant Owner",
        phone="9000000000",
    )


# ============================================================
# RESTAURANT
# ============================================================

@pytest.fixture()
def restaurant(db, owner):

    restaurant = Restaurant(
        restaurant_name="Bharath Restaurant",
        owner_id=owner.id,
        address="100 Food Street",
        city="Chennai",
        phone="9000000001",
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


# ============================================================
# CLOSED RESTAURANT
# ============================================================

@pytest.fixture()
def closed_restaurant(db, owner):

    restaurant = Restaurant(
        restaurant_name="Closed Restaurant",
        owner_id=owner.id,
        address="200 Food Street",
        city="Chennai",
        phone="9000000002",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.CLOSED,
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


# ============================================================
# MENU ITEM
# ============================================================

@pytest.fixture()
def menu_item(db, restaurant):

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Spicy chicken biryani",
        price=250.0,
        preparation_time=25,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# ============================================================
# ORDER PAYLOAD
# ============================================================

def order_payload(
    customer,
    restaurant,
    address,
    menu_item,
    **overrides,
):

    payload = {
        "customer_id": customer.id,
        "restaurant_id": restaurant.id,
        "address_id": address.id,
        "delivery_fee": 20.0,
        "discount": 10.0,
        "tax": 10.0,
        "items": [
            {
                "menu_item_id": menu_item.id,
                "quantity": 2,
            }
        ],
    }

    payload.update(overrides)

    return payload


# ============================================================
# CREATE ORDER
# ============================================================

def test_create_order(
    client,
    customer,
    restaurant,
    address,
    menu_item,
):

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            menu_item,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer.id
    assert data["restaurant_id"] == restaurant.id
    assert data["address_id"] == address.id

    assert data["subtotal"] == 500.0
    assert data["delivery_fee"] == 20.0
    assert data["discount"] == 10.0
    assert data["tax"] == 10.0
    assert data["total_amount"] == 520.0

    assert data["order_status"] == "Pending"
    assert data["payment_status"] == "Pending"

    assert len(data["items"]) == 1

    assert data["items"][0]["menu_item_id"] == menu_item.id
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == 250.0
    assert data["items"][0]["subtotal"] == 500.0


# ============================================================
# CREATE ORDER - MULTIPLE ITEMS
# ============================================================

def test_create_order_multiple_items(
    client,
    customer,
    restaurant,
    address,
    menu_item,
    db,
):

    second_item = MenuItem(
        restaurant_id=restaurant.id,
        category="Dessert",
        name="Ice Cream",
        description="Vanilla ice cream",
        price=100.0,
        preparation_time=5,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(second_item)
    db.commit()
    db.refresh(second_item)

    payload = order_payload(
        customer,
        restaurant,
        address,
        menu_item,
    )

    payload["items"].append(
        {
            "menu_item_id": second_item.id,
            "quantity": 3,
        }
    )

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["subtotal"] == 800.0
    assert data["total_amount"] == 820.0
    assert len(data["items"]) == 2


# ============================================================
# PENDING TRACKING
# ============================================================

def test_create_order_creates_pending_tracking(
    client,
    db,
    customer,
    restaurant,
    address,
    menu_item,
):

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            menu_item,
        ),
    )

    assert response.status_code == 201

    order_id = response.json()["id"]

    tracking = (
        db.query(OrderTracking)
        .filter(
            OrderTracking.order_id == order_id
        )
        .all()
    )

    assert len(tracking) == 1

    assert tracking[0].status == "Pending"
    assert tracking[0].location == restaurant.restaurant_name
    assert tracking[0].remarks == (
        "Order placed successfully"
    )


# ============================================================
# CUSTOMER NOT FOUND
# ============================================================

def test_create_order_customer_not_found(
    client,
    restaurant,
    address,
    menu_item,
):

    payload = {
        "customer_id": 9999,
        "restaurant_id": restaurant.id,
        "address_id": address.id,
        "delivery_fee": 20,
        "discount": 10,
        "tax": 10,
        "items": [
            {
                "menu_item_id": menu_item.id,
                "quantity": 1,
            }
        ],
    }

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Customer not found"
    )


# ============================================================
# RESTAURANT NOT FOUND
# ============================================================

def test_create_order_restaurant_not_found(
    client,
    customer,
    address,
    menu_item,
):

    payload = {
        "customer_id": customer.id,
        "restaurant_id": 9999,
        "address_id": address.id,
        "delivery_fee": 20,
        "discount": 10,
        "tax": 10,
        "items": [
            {
                "menu_item_id": menu_item.id,
                "quantity": 1,
            }
        ],
    }

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Restaurant not found"
    )


# ============================================================
# CLOSED RESTAURANT
# ============================================================

def test_create_order_closed_restaurant(
    client,
    customer,
    closed_restaurant,
    address,
    db,
):

    item = MenuItem(
        restaurant_id=closed_restaurant.id,
        category="Main Course",
        name="Biryani",
        description="Biryani",
        price=250,
        preparation_time=20,
        availability=True,
        vegetarian=False,
        spicy_level=SpicyLevel.MEDIUM,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            closed_restaurant,
            address,
            item,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Restaurant is closed"
    )


# ============================================================
# CUSTOMER WITHOUT ADDRESS
# ============================================================

def test_create_order_customer_without_address(
    client,
    db,
    restaurant,
    menu_item,
):

    new_user = create_user(
        db,
        "No Address User",
        "noaddress@example.com",
        phone="9111111111",
    )

    new_customer = Customer(
        user_id=new_user.id,
        name="No Address Customer",
        email="noaddresscustomer@example.com",
        phone="9111111112",
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    payload = {
        "customer_id": new_customer.id,
        "restaurant_id": restaurant.id,
        "address_id": 9999,
        "delivery_fee": 20,
        "discount": 10,
        "tax": 10,
        "items": [
            {
                "menu_item_id": menu_item.id,
                "quantity": 1,
            }
        ],
    }

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Customer has no valid delivery address"
    )


# ============================================================
# INVALID ADDRESS
# ============================================================

def test_create_order_invalid_address(
    client,
    db,
    customer,
    restaurant,
    address,
    menu_item,
):

    other_user = create_user(
        db,
        "Other User",
        "other@example.com",
        phone="9111111113",
    )

    other_customer = Customer(
        user_id=other_user.id,
        name="Other Customer",
        email="othercustomer@example.com",
        phone="9111111114",
    )

    db.add(other_customer)
    db.commit()
    db.refresh(other_customer)

    other_address = Address(
        customer_id=other_customer.id,
        address_line="Other Street",
        city="Chennai",
        pincode="600002",
        address_type="Home",
        is_default=True,
    )

    db.add(other_address)
    db.commit()
    db.refresh(other_address)

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            other_address,
            menu_item,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Address is invalid"
    )


# ============================================================
# FOOD ITEM NOT FOUND
# ============================================================

def test_create_order_food_item_not_found(
    client,
    customer,
    restaurant,
    address,
):

    payload = {
        "customer_id": customer.id,
        "restaurant_id": restaurant.id,
        "address_id": address.id,
        "delivery_fee": 20,
        "discount": 10,
        "tax": 10,
        "items": [
            {
                "menu_item_id": 9999,
                "quantity": 1,
            }
        ],
    }

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Food item not found"
    )


# ============================================================
# FOOD ITEM WRONG RESTAURANT
# ============================================================

def test_create_order_food_item_wrong_restaurant(
    client,
    db,
    customer,
    restaurant,
    address,
    owner,
):

    other_restaurant = Restaurant(
        restaurant_name="Other Restaurant",
        owner_id=owner.id,
        address="300 Food Street",
        city="Chennai",
        phone="9000000003",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
        delivery_time=30,
    )

    db.add(other_restaurant)
    db.commit()
    db.refresh(other_restaurant)

    item = MenuItem(
        restaurant_id=other_restaurant.id,
        category="Main Course",
        name="Noodles",
        description="Noodles",
        price=180,
        preparation_time=15,
        availability=True,
        vegetarian=True,
        spicy_level=SpicyLevel.MILD,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            item,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Food item does not belong to this restaurant"
    )


# ============================================================
# UNAVAILABLE FOOD ITEM
# ============================================================

def test_create_order_unavailable_food_item(
    client,
    customer,
    restaurant,
    address,
    menu_item,
    db,
):

    menu_item.availability = False
    db.commit()

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            menu_item,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Food item is unavailable"
    )


# ============================================================
# EMPTY ITEMS
# ============================================================

def test_create_order_empty_items(
    client,
    customer,
    restaurant,
    address,
    menu_item,
):

    payload = order_payload(
        customer,
        restaurant,
        address,
        menu_item,
    )

    payload["items"] = []

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# INVALID QUANTITY
# ============================================================

def test_create_order_invalid_quantity(
    client,
    customer,
    restaurant,
    address,
    menu_item,
):

    payload = order_payload(
        customer,
        restaurant,
        address,
        menu_item,
    )

    payload["items"][0]["quantity"] = 0

    response = client.post(
        "/orders",
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# NEGATIVE DELIVERY FEE
# ============================================================

def test_create_order_negative_delivery_fee(
    client,
    customer,
    restaurant,
    address,
    menu_item,
):

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            menu_item,
            delivery_fee=-1,
        ),
    )

    assert response.status_code == 422


# ============================================================
# NEGATIVE DISCOUNT
# ============================================================

def test_create_order_negative_discount(
    client,
    customer,
    restaurant,
    address,
    menu_item,
):

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            menu_item,
            discount=-1,
        ),
    )

    assert response.status_code == 422


# ============================================================
# DISCOUNT CAPPED AT SUBTOTAL
# ============================================================

def test_create_order_discount_capped(
    client,
    customer,
    restaurant,
    address,
    menu_item,
):

    response = client.post(
        "/orders",
        json=order_payload(
            customer,
            restaurant,
            address,
            menu_item,
            discount=1000,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["subtotal"] == 500.0
    assert data["discount"] == 500.0
    assert data["total_amount"] == 30.0


# ============================================================
# GET ALL ORDERS
# ============================================================

def create_order_record(
    db,
    customer,
    restaurant,
    address,
    status=OrderStatus.PENDING,
    total=280.0,
):

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=total,
        order_status=status,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def test_get_orders(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order1 = create_order_record(
        db,
        customer,
        restaurant,
        address,
        total=200,
    )

    order2 = create_order_record(
        db,
        customer,
        restaurant,
        address,
        total=300,
    )

    response = client.get(
        "/orders"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["id"] == order2.id
    assert data[1]["id"] == order1.id


# ============================================================
# GET ORDERS BY CUSTOMER
# ============================================================

def test_get_orders_by_customer(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    other_user = create_user(
        db,
        "Other",
        "another@example.com",
        phone="9111111115",
    )

    other_customer = Customer(
        user_id=other_user.id,
        name="Other Customer",
        email="anothercustomer@example.com",
        phone="9111111116",
    )

    db.add(other_customer)
    db.commit()
    db.refresh(other_customer)

    other_address = Address(
        customer_id=other_customer.id,
        address_line="Other Street",
        city="Chennai",
        pincode="600002",
        address_type="Home",
        is_default=True,
    )

    db.add(other_address)
    db.commit()
    db.refresh(other_address)

    create_order_record(
        db,
        other_customer,
        restaurant,
        other_address,
    )

    response = client.get(
        f"/orders?customer_id={customer.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == order.id


# ============================================================
# INVALID CUSTOMER FILTER
# ============================================================

def test_get_orders_invalid_customer_id(
    client,
):

    response = client.get(
        "/orders?customer_id=0"
    )

    assert response.status_code == 422


# ============================================================
# GET SINGLE ORDER
# ============================================================

def test_get_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.get(
        f"/orders/{order.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == order.id


# ============================================================
# ORDER NOT FOUND
# ============================================================

def test_get_order_not_found(
    client,
):

    response = client.get(
        "/orders/9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


# ============================================================
# SEARCH BY STATUS
# ============================================================

def test_search_orders_by_status(
    client,
    customer,
    restaurant,
    address,
    db,
):

    create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.PENDING,
    )

    create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.ACCEPTED,
    )

    response = client.get(
        "/orders/search?status=Accepted"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["order_status"] == "Accepted"


# ============================================================
# SEARCH BY PAYMENT STATUS
# ============================================================

def test_search_orders_by_payment_status(
    client,
    customer,
    restaurant,
    address,
    db,
):

    create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    paid_order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    paid_order.payment_status = PaymentStatus.PAID

    db.commit()

    response = client.get(
        "/orders/search?payment_status=Paid"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == paid_order.id


# ============================================================
# SEARCH BY RESTAURANT
# ============================================================

def test_search_orders_by_restaurant(
    client,
    customer,
    restaurant,
    address,
    db,
):

    create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.get(
        f"/orders/search?restaurant_id={restaurant.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_id"] == restaurant.id


# ============================================================
# SEARCH SORT TOTAL ASC
# ============================================================

def test_search_orders_sort_total_ascending(
    client,
    customer,
    restaurant,
    address,
    db,
):

    create_order_record(
        db,
        customer,
        restaurant,
        address,
        total=400,
    )

    create_order_record(
        db,
        customer,
        restaurant,
        address,
        total=200,
    )

    create_order_record(
        db,
        customer,
        restaurant,
        address,
        total=300,
    )

    response = client.get(
        "/orders/search"
        "?sort_by=total_amount"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["total_amount"]
        for item in data
    ] == [
        200.0,
        300.0,
        400.0,
    ]


# ============================================================
# SEARCH SORT ID DESC
# ============================================================

def test_search_orders_sort_id_desc(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order1 = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    order2 = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.get(
        "/orders/search"
        "?sort_by=id"
        "&sort_order=desc"
    )

    assert response.status_code == 200

    data = response.json()

    assert data[0]["id"] == order2.id
    assert data[1]["id"] == order1.id


# ============================================================
# SEARCH PAGINATION
# ============================================================

def test_search_orders_pagination(
    client,
    customer,
    restaurant,
    address,
    db,
):

    for index in range(5):

        create_order_record(
            db,
            customer,
            restaurant,
            address,
            total=100 + index,
        )

    response = client.get(
        "/orders/search"
        "?page=2"
        "&limit=2"
        "&sort_by=total_amount"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert [
        item["total_amount"]
        for item in data
    ] == [
        102.0,
        103.0,
    ]


# ============================================================
# SEARCH INVALID PAGE
# ============================================================

def test_search_orders_invalid_page(
    client,
):

    response = client.get(
        "/orders/search?page=0"
    )

    assert response.status_code == 422


# ============================================================
# SEARCH INVALID LIMIT
# ============================================================

def test_search_orders_invalid_limit(
    client,
):

    response = client.get(
        "/orders/search?limit=101"
    )

    assert response.status_code == 422


# ============================================================
# SEARCH INVALID RESTAURANT ID
# ============================================================

def test_search_orders_invalid_restaurant_id(
    client,
):

    response = client.get(
        "/orders/search?restaurant_id=0"
    )

    assert response.status_code == 422


# ============================================================
# DELIVERY PARTNER HELPER
# ============================================================

def create_partner(
    db,
    phone="9888888888",
    vehicle="TN01AB1234",
):

    partner = DeliveryPartner(
        name="Delivery Partner",
        phone=phone,
        vehicle_type="Bike",
        vehicle_number=vehicle,
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    return partner


# ============================================================
# ASSIGN DRIVER
# ============================================================

def test_assign_driver(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    partner = create_partner(
        db
    )

    response = client.post(
        f"/orders/{order.id}/assign-driver"
        f"?partner_id={partner.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["delivery_partner_id"] == partner.id
    assert data["order_status"] == (
        "Out for Delivery"
    )


# ============================================================
# ASSIGN DRIVER - ORDER NOT FOUND
# ============================================================

def test_assign_driver_order_not_found(
    client,
    db,
):

    partner = create_partner(
        db
    )

    response = client.post(
        f"/orders/9999/assign-driver"
        f"?partner_id={partner.id}"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


# ============================================================
# ASSIGN DRIVER - PARTNER NOT FOUND
# ============================================================

def test_assign_driver_partner_not_found(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.post(
        f"/orders/{order.id}/assign-driver"
        "?partner_id=9999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Delivery partner not found"
    )


# ============================================================
# ASSIGN DRIVER - MISSING PARTNER ID
# ============================================================

def test_assign_driver_missing_partner_id(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.post(
        f"/orders/{order.id}/assign-driver"
    )

    assert response.status_code == 422


# ============================================================
# COMPLETE DELIVERY
# ============================================================

def test_complete_delivery(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.OUT_FOR_DELIVERY,
    )

    partner = create_partner(
        db
    )

    order.delivery_partner_id = partner.id

    db.commit()

    response = client.post(
        f"/orders/{order.id}/deliver"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_status"] == (
        "Delivered"
    )

    db.refresh(partner)

    assert partner.availability_status == (
        DeliveryPartnerStatus.AVAILABLE
    )


# ============================================================
# COMPLETE DELIVERY WITHOUT PARTNER
# ============================================================

def test_complete_delivery_without_partner(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.post(
        f"/orders/{order.id}/deliver"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "No delivery partner assigned to this order"
    )


# ============================================================
# COMPLETE CANCELLED ORDER
# ============================================================

def test_complete_cancelled_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.CANCELLED,
    )

    partner = create_partner(
        db
    )

    order.delivery_partner_id = partner.id

    db.commit()

    response = client.post(
        f"/orders/{order.id}/deliver"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Cancelled order cannot be delivered"
    )


# ============================================================
# DELIVERY TRACKING
# ============================================================

def test_complete_delivery_creates_tracking(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.OUT_FOR_DELIVERY,
    )

    partner = create_partner(
        db
    )

    order.delivery_partner_id = partner.id

    db.commit()

    response = client.post(
        f"/orders/{order.id}/deliver"
    )

    assert response.status_code == 200

    tracking = (
        db.query(OrderTracking)
        .filter(
            OrderTracking.order_id == order.id
        )
        .order_by(
            OrderTracking.id.desc()
        )
        .first()
    )

    assert tracking.status == "Delivered"
    assert tracking.location == "Chennai"
    assert tracking.remarks == (
        "Order delivered successfully"
    )


# ============================================================
# CANCEL PENDING ORDER
# ============================================================

def test_cancel_pending_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.PENDING,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Changed my mind"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_status"] == (
        "Cancelled"
    )


# ============================================================
# CANCEL ORDER HISTORY
# ============================================================

def test_cancel_order_creates_history(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Customer requested cancellation"
        },
    )

    assert response.status_code == 200

    history = (
        db.query(CancellationHistory)
        .filter(
            CancellationHistory.order_id == order.id
        )
        .first()
    )

    assert history is not None
    assert history.previous_status == "Pending"
    assert history.cancellation_reason == (
        "Customer requested cancellation"
    )
    assert history.refund_amount == 0.0


# ============================================================
# CANCEL DELIVERED ORDER
# ============================================================

def test_cancel_delivered_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.DELIVERED,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Too late"
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Delivered orders cannot be cancelled"
    )


# ============================================================
# CANCEL ALREADY CANCELLED
# ============================================================

def test_cancel_already_cancelled_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.CANCELLED,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Again"
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order is already cancelled"
    )


# ============================================================
# CANCEL READY ORDER
# ============================================================

def test_cancel_ready_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.READY,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Cancel"
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order cannot be cancelled at this stage"
    )


# ============================================================
# CANCEL PICKED UP ORDER
# ============================================================

def test_cancel_picked_up_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.PICKED_UP,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Cancel"
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order cannot be cancelled at this stage"
    )


# ============================================================
# CANCEL OUT FOR DELIVERY
# ============================================================

def test_cancel_out_for_delivery_order(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
        status=OrderStatus.OUT_FOR_DELIVERY,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "Cancel"
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order cannot be cancelled at this stage"
    )


# ============================================================
# CANCEL ORDER NOT FOUND
# ============================================================

def test_cancel_order_not_found(
    client,
):

    response = client.post(
        "/orders/9999/cancel",
        json={
            "reason": "Not found"
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


# ============================================================
# CANCEL WITHOUT REASON
# ============================================================

def test_cancel_order_without_reason(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={},
    )

    assert response.status_code == 200

    assert response.json()["order_status"] == (
        "Cancelled"
    )


# ============================================================
# CANCEL REASON TOO LONG
# ============================================================

def test_cancel_reason_too_long(
    client,
    customer,
    restaurant,
    address,
    db,
):

    order = create_order_record(
        db,
        customer,
        restaurant,
        address,
    )

    response = client.post(
        f"/orders/{order.id}/cancel",
        json={
            "reason": "x" * 501
        },
    )

    assert response.status_code == 422