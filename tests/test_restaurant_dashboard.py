from datetime import datetime, timedelta, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

from app.models.user import User
from app.models.customer import Customer, Address
from app.models.restaurant import Restaurant, RestaurantStatus
from app.models.menu import MenuItem, SpicyLevel
from app.models.order import OrderStatus


# ============================================================
# TEST DATABASE
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
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
# DATABASE FIXTURE
# ============================================================

@pytest.fixture
def db():

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================
# RESTAURANT OWNER
# ============================================================

@pytest.fixture
def owner(db):

    owner = User(
        name="Restaurant Owner",
        email="owner@gmail.com",
        phone="9000000000",
        password_hash="hashed-password",
        role="Restaurant Owner",
        is_active=True,
        is_deleted=False,
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    return owner


# ============================================================
# CUSTOMER
# ============================================================

@pytest.fixture
def customer(db):

    user = User(
        name="Customer User",
        email="customer_user@gmail.com",
        phone="9000000001",
        password_hash="hashed-password",
        role="Customer",
        is_active=True,
        is_deleted=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    customer = Customer(
        user_id=user.id,
        name="Test Customer",
        email="testcustomer@gmail.com",
        phone="9000000002",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


# ============================================================
# ADDRESS
# ============================================================

@pytest.fixture
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
# RESTAURANT
# ============================================================

@pytest.fixture
def restaurant(db, owner):

    restaurant = Restaurant(
        restaurant_name="Dashboard Restaurant",
        owner_id=owner.id,
        address="123 Main Street",
        city="Chennai",
        phone="9000000010",
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

    return restaurant


# ============================================================
# MENU ITEM
# ============================================================

@pytest.fixture
def menu_item(db, restaurant):

    item = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Chicken biryani",
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
# TEST 1
# TODAY'S ORDERS
# ============================================================

def test_today_orders(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order

    # ---------------------------------------------------------
    # Create today's order
    # ---------------------------------------------------------
    today_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )

    db.add(today_order)

    # ---------------------------------------------------------
    # Create an old order
    # ---------------------------------------------------------
    old_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow() - timedelta(days=1),
    )

    db.add(old_order)

    db.commit()
    db.refresh(today_order)
    db.refresh(old_order)

    # ---------------------------------------------------------
    # Create access token for restaurant owner
    # ---------------------------------------------------------
    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # ---------------------------------------------------------
    # Call dashboard API
    # ---------------------------------------------------------
    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/today-orders",
        headers=headers,
    )

    # ---------------------------------------------------------
    # Verify response
    # ---------------------------------------------------------
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) == 1

    assert data[0]["id"] == today_order.id

    assert data[0]["restaurant_id"] == restaurant.id

    assert data[0]["customer_id"] == customer.id

    assert data[0]["total_amount"] == 300.0
    
# ============================================================
# TEST 2
# PENDING ORDERS
# ============================================================

def test_pending_orders(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order

    # ---------------------------------------------------------
    # Create pending order
    # ---------------------------------------------------------
    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )

    db.add(pending_order)

    # ---------------------------------------------------------
    # Create accepted order
    # ---------------------------------------------------------
    accepted_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )

    db.add(accepted_order)

    db.commit()

    db.refresh(pending_order)
    db.refresh(accepted_order)

    # ---------------------------------------------------------
    # Create owner access token
    # ---------------------------------------------------------
    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # ---------------------------------------------------------
    # Call pending orders API
    # ---------------------------------------------------------
    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/pending-orders",
        headers=headers,
    )

    # ---------------------------------------------------------
    # Verify response
    # ---------------------------------------------------------
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) == 1

    assert data[0]["id"] == pending_order.id

    assert data[0]["restaurant_id"] == restaurant.id

    assert data[0]["customer_id"] == customer.id

    assert data[0]["order_status"] == "Pending"

    assert data[0]["total_amount"] == 300.0
    
def test_completed_orders(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order
    from app.models.order import OrderStatus

    completed_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )
    db.add(completed_order)

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=250.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )
    db.add(pending_order)

    db.commit()
    db.refresh(completed_order)
    db.refresh(pending_order)

    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/completed-orders",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == completed_order.id
    assert data[0]["restaurant_id"] == restaurant.id
    assert data[0]["customer_id"] == customer.id
    assert data[0]["order_status"] == "Delivered"
    assert data[0]["total_amount"] == 300.0
    
def test_cancelled_orders(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order
    from app.models.order import OrderStatus

    cancelled_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )
    db.add(cancelled_order)

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=250.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )
    db.add(pending_order)

    db.commit()
    db.refresh(cancelled_order)
    db.refresh(pending_order)

    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/cancelled-orders",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == cancelled_order.id
    assert data[0]["restaurant_id"] == restaurant.id
    assert data[0]["customer_id"] == customer.id
    assert data[0]["order_status"] == "Cancelled"
    assert data[0]["total_amount"] == 300.0
    
def test_today_revenue(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order
    from app.models.order import OrderStatus

    delivered_order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    delivered_order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=150.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=200.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=150.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )

    db.add_all([
        delivered_order_1,
        delivered_order_2,
        pending_order,
    ])
    db.commit()

    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/today-revenue",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == restaurant.id
    assert data["total_revenue"] == 500.0
    
def test_monthly_revenue(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order
    from app.models.order import OrderStatus

    current_month_order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    current_month_order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=150.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=200.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=150.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime.utcnow(),
    )

    db.add_all([
        current_month_order_1,
        current_month_order_2,
        pending_order,
    ])
    db.commit()

    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/monthly-revenue",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == restaurant.id
    assert data["total_revenue"] == 500.0
    
def test_most_ordered_food(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order, OrderItem
    from app.models.order import OrderStatus

    most_ordered_item = menu_item

    delivered_order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=550.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    delivered_order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=350.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    db.add_all([
        delivered_order_1,
        delivered_order_2,
    ])
    db.commit()

    db.refresh(delivered_order_1)
    db.refresh(delivered_order_2)

    item_1 = OrderItem(
        order_id=delivered_order_1.id,
        menu_item_id=most_ordered_item.id,
        quantity=3,
        unit_price=100.0,
        subtotal=300.0,
    )

    item_2 = OrderItem(
        order_id=delivered_order_2.id,
        menu_item_id=most_ordered_item.id,
        quantity=5,
        unit_price=100.0,
        subtotal=500.0,
    )

    db.add_all([
        item_1,
        item_2,
    ])
    db.commit()

    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/most-ordered-food",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == restaurant.id
    assert data["menu_item_id"] == most_ordered_item.id
    assert data["total_quantity"] == 8
    
def test_average_rating(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order
    from app.models.order import OrderStatus
    from app.models.review import Review

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    review_1 = Review(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        order_id=order.id,
        rating=5,
    )

    review_2 = Review(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        order_id=order.id,
        rating=4,
    )

    db.add_all([
        review_1,
        review_2,
    ])
    db.commit()

    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/average-rating",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == restaurant.id
    assert data["average_rating"] == 4.5
    
def test_total_customers(
    client,
    db,
    owner,
    customer,
    restaurant,
    menu_item,
    address,
):
    from app.models.order import Order
    from app.models.order import OrderStatus
    from app.models.user import User
    from app.models.customer import Customer

    # Create second user
    customer_2_user = User(
        name="Customer Two",
        email="customer2@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_2_user)
    db.commit()
    db.refresh(customer_2_user)

    # Create second customer
    customer_2 = Customer(
        user_id=customer_2_user.id,
        name="Customer Two",
        email="customer2@gmail.com",
        phone="9876543211",
    )

    db.add(customer_2)
    db.commit()
    db.refresh(customer_2)

    # Customer 1 - Order 1
    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    # Customer 1 - Order 2
    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=150.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=200.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    # Customer 2 - Order 1
    order_3 = Order(
        customer_id=customer_2.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=40.0,
        discount=0.0,
        tax=10.0,
        total_amount=250.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime.utcnow(),
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    # Create access token for restaurant owner
    from app.services.auth_service import create_access_token

    token = create_access_token(
        user_id=owner.id,
        role=owner.role,
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Call Total Customers API
    response = client.get(
        f"/restaurant-dashboard/{restaurant.id}/total-customers",
        headers=headers,
    )

    # Verify response
    assert response.status_code == 200

    data = response.json()

    assert data["restaurant_id"] == restaurant.id
    assert data["total_customers"] == 2