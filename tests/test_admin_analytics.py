from datetime import time, datetime
from app.models.order import Order, OrderStatus
from sqlalchemy import func
from sqlalchemy.orm import Session

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.restaurant import Restaurant
from app.models.user import User
from app.services.auth_service import create_access_token


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

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

        # Reset database after every test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin(db, request):
    user = User(
        name="Admin User",
        email=f"{request.node.name}@fooddelivery.com",
        password_hash="test_password_hash",
        role="Admin",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# =========================================================
# STEP 1 - TOTAL RESTAURANTS
# =========================================================

def test_total_restaurants(
    client,
    db,
    admin,
):
    restaurant_1 = Restaurant(
        restaurant_name="Restaurant One",
        owner_id=admin.id,
        address="Chennai Main Road",
        city="Chennai",
        phone="9876543210",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    restaurant_2 = Restaurant(
        restaurant_name="Restaurant Two",
        owner_id=admin.id,
        address="Chennai Central",
        city="Chennai",
        phone="9876543211",
        cuisine_type="Chinese",
        opening_time=time(10, 0),
        closing_time=time(23, 0),
        delivery_radius=12.0,
        delivery_time=35,
    )

    db.add_all([
        restaurant_1,
        restaurant_2,
    ])

    db.commit()

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        "/admin-analytics/total-restaurants",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_restaurants"] == 2


# =========================================================
# STEP 2 - TOTAL CUSTOMERS
# =========================================================

def test_total_customers(
    client,
    db,
    admin,
):
    from app.models.customer import Customer

    customer_1 = Customer(
        name="Customer One",
        email="customer1@gmail.com",
        phone="9876543210",
    )

    customer_2 = Customer(
        name="Customer Two",
        email="customer2@gmail.com",
        phone="9876543211",
    )

    db.add_all([
        customer_1,
        customer_2,
    ])

    db.commit()

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        "/admin-analytics/total-customers",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_customers"] == 2


# =========================================================
# STEP 3 - TOTAL ORDERS
# =========================================================

def test_total_orders(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Order Customer",
        email="ordercustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Order Customer",
        email="ordercustomer@gmail.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Customer Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="123 Main Street",
        city="Chennai",
        pincode="600001",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Order Test Restaurant",
        owner_id=admin.id,
        address="456 Restaurant Street",
        city="Chennai",
        phone="9876543212",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Three Orders
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Total Orders API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/total-orders",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 3


# =========================================================
# STEP 4 - TOTAL REVENUE
# =========================================================

def test_total_revenue(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Revenue Customer",
        email="revenuecustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Revenue Customer",
        email="revenuecustomer@gmail.com",
        phone="9876543220",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Customer Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="789 Revenue Street",
        city="Chennai",
        pincode="600002",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Revenue Test Restaurant",
        owner_id=admin.id,
        address="789 Restaurant Street",
        city="Chennai",
        phone="9876543221",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Three Orders
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Total Revenue API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/total-revenue",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_revenue"] == 690.0


# =========================================================
# STEP 5 - TOTAL REFUNDS
# =========================================================

def test_total_refunds(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address
    from app.models.restaurant import Restaurant
    from app.models.payment import (
        Payment,
        PaymentMethod,
        PaymentStatus,
    )
    from app.models.refund import Refund

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Refund Customer",
        email="refundcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Refund Customer",
        email="refundcustomer@gmail.com",
        phone="9876543230",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="100 Refund Street",
        city="Chennai",
        pincode="600003",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Refund Test Restaurant",
        owner_id=admin.id,
        address="100 Restaurant Street",
        city="Chennai",
        phone="9876543231",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Order
    # ---------------------------------------------------------

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=25.0,
        total_amount=545.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # ---------------------------------------------------------
    # 6. Create Payment
    # ---------------------------------------------------------

    payment = Payment(
        order_id=order.id,
        amount=545.0,
        payment_method=PaymentMethod.UPI,
        transaction_id="REFUND-TXN-001",
        payment_status=PaymentStatus.REFUNDED,
        paid_at=datetime.utcnow(),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # ---------------------------------------------------------
    # 7. Create Refund
    # ---------------------------------------------------------

    refund = Refund(
        payment_id=payment.id,
        order_id=order.id,
        amount=545.0,
        refund_status="Success",
        reason="Order cancelled",
        refunded_at=datetime.utcnow(),
    )

    db.add(refund)
    db.commit()
    db.refresh(refund)

    # ---------------------------------------------------------
    # 8. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 9. Call Total Refunds API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/total-refunds",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 10. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_refunds"] == 545.0
    
# =========================================================
# STEP 6 - ACTIVE DELIVERY PARTNERS
# =========================================================

def test_active_delivery_partners(
    client,
    db,
    admin,
):
    from app.models.delivery_partner import (
        DeliveryPartner,
        DeliveryPartnerStatus,
    )

    # ---------------------------------------------------------
    # 1. Create Delivery Partners
    # ---------------------------------------------------------

    partner_1 = DeliveryPartner(
        name="Delivery Partner One",
        phone="9876500001",
        vehicle_type="Bike",
        vehicle_number="TN01AB1001",
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    partner_2 = DeliveryPartner(
        name="Delivery Partner Two",
        phone="9876500002",
        vehicle_type="Bike",
        vehicle_number="TN01AB1002",
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    partner_3 = DeliveryPartner(
        name="Delivery Partner Three",
        phone="9876500003",
        vehicle_type="Car",
        vehicle_number="TN01AB1003",
        availability_status=DeliveryPartnerStatus.BUSY,
        current_location="Chennai",
    )

    partner_4 = DeliveryPartner(
        name="Delivery Partner Four",
        phone="9876500004",
        vehicle_type="Bike",
        vehicle_number="TN01AB1004",
        availability_status=DeliveryPartnerStatus.OFFLINE,
        current_location="Chennai",
    )

    db.add_all([
        partner_1,
        partner_2,
        partner_3,
        partner_4,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 2. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 3. Call Active Delivery Partners API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/active-delivery-partners",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 4. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["active_delivery_partners"] == 2
    
# =========================================================
# STEP 7 - TOP RESTAURANTS
# =========================================================

def test_top_restaurants(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Top Restaurant Customer",
        email="toprestaurantcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Top Restaurant Customer",
        email="toprestaurantcustomer@gmail.com",
        phone="9876543240",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Top Restaurant Street",
        city="Chennai",
        pincode="600004",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurants
    # ---------------------------------------------------------

    restaurant_1 = Restaurant(
        restaurant_name="Top Restaurant One",
        owner_id=admin.id,
        address="Restaurant One Street",
        city="Chennai",
        phone="9876543241",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    restaurant_2 = Restaurant(
        restaurant_name="Top Restaurant Two",
        owner_id=admin.id,
        address="Restaurant Two Street",
        city="Chennai",
        phone="9876543242",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    restaurant_3 = Restaurant(
        restaurant_name="Top Restaurant Three",
        owner_id=admin.id,
        address="Restaurant Three Street",
        city="Chennai",
        phone="9876543243",
        cuisine_type="Italian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add_all([
        restaurant_1,
        restaurant_2,
        restaurant_3,
    ])

    db.commit()

    db.refresh(restaurant_1)
    db.refresh(restaurant_2)
    db.refresh(restaurant_3)

    # ---------------------------------------------------------
    # 5. Create Delivered Orders
    #
    # Restaurant One  -> 3 delivered orders
    # Restaurant Two  -> 2 delivered orders
    # Restaurant Three -> 1 delivered order
    # ---------------------------------------------------------

    orders = [
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_1.id,
            address_id=address.id,
            subtotal=100.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=125.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_1.id,
            address_id=address.id,
            subtotal=150.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=175.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_1.id,
            address_id=address.id,
            subtotal=200.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=230.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_2.id,
            address_id=address.id,
            subtotal=120.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=145.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_2.id,
            address_id=address.id,
            subtotal=180.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=210.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_3.id,
            address_id=address.id,
            subtotal=100.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=125.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
    ]

    db.add_all(orders)
    db.commit()

    # ---------------------------------------------------------
    # 6. Create Non-Delivered Order
    #
    # This should NOT affect restaurant ranking.
    # ---------------------------------------------------------

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant_3.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    db.add(pending_order)
    db.commit()

    # ---------------------------------------------------------
    # 7. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 8. Call Top Restaurants API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/top-restaurants",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 9. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "top_restaurants" in data

    assert len(data["top_restaurants"]) == 3

    assert data["top_restaurants"][0]["restaurant_id"] == restaurant_1.id
    assert data["top_restaurants"][0]["restaurant_name"] == "Top Restaurant One"
    assert data["top_restaurants"][0]["total_orders"] == 3

    assert data["top_restaurants"][1]["restaurant_id"] == restaurant_2.id
    assert data["top_restaurants"][1]["restaurant_name"] == "Top Restaurant Two"
    assert data["top_restaurants"][1]["total_orders"] == 2

    assert data["top_restaurants"][2]["restaurant_id"] == restaurant_3.id
    assert data["top_restaurants"][2]["restaurant_name"] == "Top Restaurant Three"
    assert data["top_restaurants"][2]["total_orders"] == 1
    
# =========================================================
# STEP 8 - TOP FOOD ITEMS
# =========================================================

def test_top_food_items(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus, OrderItem
    from app.models.user import User
    from app.models.customer import Customer, Address
    from app.models.menu import MenuItem

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Food Item Customer",
        email="fooditemcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Food Item Customer",
        email="fooditemcustomer@gmail.com",
        phone="9876543250",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Food Item Street",
        city="Chennai",
        pincode="600005",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Food Item Restaurant",
        owner_id=admin.id,
        address="Food Restaurant Street",
        city="Chennai",
        phone="9876543251",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Menu Items
    # ---------------------------------------------------------

    biryani = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Chicken biryani",
        price=250.0,
        preparation_time=30,
        availability=True,
        vegetarian=False,
    )

    pizza = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Veg Pizza",
        description="Vegetable pizza",
        price=200.0,
        preparation_time=25,
        availability=True,
        vegetarian=True,
    )

    burger = MenuItem(
        restaurant_id=restaurant.id,
        category="Fast Food",
        name="Chicken Burger",
        description="Chicken burger",
        price=150.0,
        preparation_time=20,
        availability=True,
        vegetarian=False,
    )

    db.add_all([
        biryani,
        pizza,
        burger,
    ])

    db.commit()

    db.refresh(biryani)
    db.refresh(pizza)
    db.refresh(burger)

    # ---------------------------------------------------------
    # 6. Create Delivered Orders
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=650.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=30.0,
        total_amount=700.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=550.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=25.0,
        total_amount=595.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    db.refresh(order_1)
    db.refresh(order_2)
    db.refresh(order_3)

    # ---------------------------------------------------------
    # 7. Create Order Items
    #
    # Chicken Biryani -> 8
    # Veg Pizza       -> 5
    # Chicken Burger  -> 2
    # ---------------------------------------------------------

    items = [
        OrderItem(
            order_id=order_1.id,
            menu_item_id=biryani.id,
            quantity=3,
            unit_price=250.0,
            subtotal=750.0,
        ),
        OrderItem(
            order_id=order_1.id,
            menu_item_id=pizza.id,
            quantity=2,
            unit_price=200.0,
            subtotal=400.0,
        ),
        OrderItem(
            order_id=order_2.id,
            menu_item_id=biryani.id,
            quantity=5,
            unit_price=250.0,
            subtotal=1250.0,
        ),
        OrderItem(
            order_id=order_2.id,
            menu_item_id=pizza.id,
            quantity=3,
            unit_price=200.0,
            subtotal=600.0,
        ),
        OrderItem(
            order_id=order_3.id,
            menu_item_id=pizza.id,
            quantity=0,
            unit_price=200.0,
            subtotal=0.0,
        ),
        OrderItem(
            order_id=order_3.id,
            menu_item_id=burger.id,
            quantity=2,
            unit_price=150.0,
            subtotal=300.0,
        ),
    ]

    # Remove the zero-quantity item because quantity represents
    # actual ordered units.
    items = [
        item for item in items
        if item.quantity > 0
    ]

    db.add_all(items)
    db.commit()

    # ---------------------------------------------------------
    # 8. Create Pending Order
    #
    # This must NOT affect the ranking.
    # ---------------------------------------------------------

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=280.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    db.add(pending_order)
    db.commit()

    pending_item = OrderItem(
        order_id=pending_order.id,
        menu_item_id=burger.id,
        quantity=100,
        unit_price=150.0,
        subtotal=15000.0,
    )

    db.add(pending_item)
    db.commit()

    # ---------------------------------------------------------
    # 9. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 10. Call Top Food Items API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/top-food-items",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 11. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "top_food_items" in data

    assert len(data["top_food_items"]) == 3

    assert data["top_food_items"][0]["menu_item_id"] == biryani.id
    assert data["top_food_items"][0]["food_name"] == "Chicken Biryani"
    assert data["top_food_items"][0]["total_quantity"] == 8

    assert data["top_food_items"][1]["menu_item_id"] == pizza.id
    assert data["top_food_items"][1]["food_name"] == "Veg Pizza"
    assert data["top_food_items"][1]["total_quantity"] == 5

    assert data["top_food_items"][2]["menu_item_id"] == burger.id
    assert data["top_food_items"][2]["food_name"] == "Chicken Burger"
    assert data["top_food_items"][2]["total_quantity"] == 2
    
# =========================================================
# STEP 9 - MOST POPULAR CUISINE
# =========================================================

def test_most_popular_cuisine(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Cuisine Customer",
        email="cuisinecustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Cuisine Customer",
        email="cuisinecustomer@gmail.com",
        phone="9876543260",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Cuisine Street",
        city="Chennai",
        pincode="600006",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurants
    #
    # Indian  -> 4 delivered orders
    # Chinese -> 2 delivered orders
    # Italian -> 1 delivered order
    # ---------------------------------------------------------

    indian_restaurant = Restaurant(
        restaurant_name="Indian Cuisine Restaurant",
        owner_id=admin.id,
        address="Indian Restaurant Street",
        city="Chennai",
        phone="9876543261",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    chinese_restaurant = Restaurant(
        restaurant_name="Chinese Cuisine Restaurant",
        owner_id=admin.id,
        address="Chinese Restaurant Street",
        city="Chennai",
        phone="9876543262",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    italian_restaurant = Restaurant(
        restaurant_name="Italian Cuisine Restaurant",
        owner_id=admin.id,
        address="Italian Restaurant Street",
        city="Chennai",
        phone="9876543263",
        cuisine_type="Italian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add_all([
        indian_restaurant,
        chinese_restaurant,
        italian_restaurant,
    ])

    db.commit()

    db.refresh(indian_restaurant)
    db.refresh(chinese_restaurant)
    db.refresh(italian_restaurant)

    # ---------------------------------------------------------
    # 5. Create Delivered Orders
    # ---------------------------------------------------------

    delivered_orders = [
        # Indian - 4 orders
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=100.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=125.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=150.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=175.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=200.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=230.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=250.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=280.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),

        # Chinese - 2 orders
        Order(
            customer_id=customer.id,
            restaurant_id=chinese_restaurant.id,
            address_id=address.id,
            subtotal=120.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=145.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=chinese_restaurant.id,
            address_id=address.id,
            subtotal=180.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=210.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),

        # Italian - 1 order
        Order(
            customer_id=customer.id,
            restaurant_id=italian_restaurant.id,
            address_id=address.id,
            subtotal=200.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=230.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
    ]

    db.add_all(delivered_orders)
    db.commit()

    # ---------------------------------------------------------
    # 6. Create Non-Delivered Orders
    #
    # These must NOT affect cuisine popularity.
    # ---------------------------------------------------------

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=chinese_restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=25.0,
        total_amount=545.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    cancelled_order = Order(
        customer_id=customer.id,
        restaurant_id=italian_restaurant.id,
        address_id=address.id,
        subtotal=600.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=30.0,
        total_amount=650.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
    )

    db.add_all([
        pending_order,
        cancelled_order,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 7. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 8. Call Most Popular Cuisine API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/most-popular-cuisine",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 9. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["cuisine_type"] == "Indian"
    assert data["total_orders"] == 4
    
# =========================================================
# STEP 10 - DAILY ORDERS
# =========================================================

def test_daily_orders(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Daily Orders Customer",
        email="dailyorderscustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Daily Orders Customer",
        email="dailyorderscustomer@gmail.com",
        phone="9876543270",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Daily Orders Street",
        city="Chennai",
        pincode="600007",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Daily Orders Restaurant",
        owner_id=admin.id,
        address="Daily Orders Restaurant Street",
        city="Chennai",
        phone="9876543271",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Orders
    #
    # 2026-09-10 -> 3 orders
    # 2026-09-11 -> 2 orders
    # 2026-09-12 -> 1 order
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime(2026, 9, 10, 10, 0, 0),
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=150.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=175.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 10, 12, 0, 0),
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 10, 18, 0, 0),
    )

    order_4 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=120.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=145.0,
        order_status=OrderStatus.PREPARING,
        payment_status="Paid",
        created_at=datetime(2026, 9, 11, 11, 0, 0),
    )

    order_5 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=180.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=210.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
        created_at=datetime(2026, 9, 11, 19, 0, 0),
    )

    order_6 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=280.0,
        order_status=OrderStatus.OUT_FOR_DELIVERY,
        payment_status="Paid",
        created_at=datetime(2026, 9, 12, 15, 0, 0),
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
        order_4,
        order_5,
        order_6,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Daily Orders API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/daily-orders",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "daily_orders" in data

    assert len(data["daily_orders"]) == 3

    # ---------------------------------------------------------
    # 9. Verify 2026-09-10
    # ---------------------------------------------------------

    assert data["daily_orders"][0]["date"] == "2026-09-10"
    assert data["daily_orders"][0]["total_orders"] == 3

    # ---------------------------------------------------------
    # 10. Verify 2026-09-11
    # ---------------------------------------------------------

    assert data["daily_orders"][1]["date"] == "2026-09-11"
    assert data["daily_orders"][1]["total_orders"] == 2

    # ---------------------------------------------------------
    # 11. Verify 2026-09-12
    # ---------------------------------------------------------

    assert data["daily_orders"][2]["date"] == "2026-09-12"
    assert data["daily_orders"][2]["total_orders"] == 1
    
# =========================================================
# STEP 11 - MONTHLY REVENUE
# =========================================================

def test_monthly_revenue(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Monthly Revenue Customer",
        email="monthlyrevenuecustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Monthly Revenue Customer",
        email="monthlyrevenuecustomer@gmail.com",
        phone="9876543280",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Monthly Revenue Street",
        city="Chennai",
        pincode="600008",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Monthly Revenue Restaurant",
        owner_id=admin.id,
        address="Monthly Revenue Restaurant Street",
        city="Chennai",
        phone="9876543281",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Orders
    #
    # August 2026:
    # 100 + 200 + 300 = 600
    #
    # September 2026:
    # 400 + 500 = 900
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=80.0,
        delivery_fee=10.0,
        discount=0.0,
        tax=10.0,
        total_amount=100.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 8, 5, 10, 0, 0),
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=170.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=200.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 8, 15, 12, 0, 0),
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=30.0,
        discount=0.0,
        tax=20.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 8, 25, 18, 0, 0),
    )

    order_4 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=350.0,
        delivery_fee=30.0,
        discount=0.0,
        tax=20.0,
        total_amount=400.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 5, 11, 0, 0),
    )

    order_5 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=450.0,
        delivery_fee=30.0,
        discount=0.0,
        tax=20.0,
        total_amount=500.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 15, 19, 0, 0),
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
        order_4,
        order_5,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Monthly Revenue API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/monthly-revenue",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "monthly_revenue" in data

    assert len(data["monthly_revenue"]) == 2

    # ---------------------------------------------------------
    # 9. Verify August 2026
    # ---------------------------------------------------------

    assert data["monthly_revenue"][0]["month"] == "2026-08"
    assert data["monthly_revenue"][0]["total_revenue"] == 600.0

    # ---------------------------------------------------------
    # 10. Verify September 2026
    # ---------------------------------------------------------

    assert data["monthly_revenue"][1]["month"] == "2026-09"
    assert data["monthly_revenue"][1]["total_revenue"] == 900.0
    
from datetime import time, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.restaurant import Restaurant
from app.models.user import User
from app.services.auth_service import create_access_token


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

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

        # Reset database after every test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin(db, request):
    user = User(
        name="Admin User",
        email=f"{request.node.name}@fooddelivery.com",
        password_hash="test_password_hash",
        role="Admin",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# =========================================================
# STEP 1 - TOTAL RESTAURANTS
# =========================================================

def test_total_restaurants(
    client,
    db,
    admin,
):
    restaurant_1 = Restaurant(
        restaurant_name="Restaurant One",
        owner_id=admin.id,
        address="Chennai Main Road",
        city="Chennai",
        phone="9876543210",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    restaurant_2 = Restaurant(
        restaurant_name="Restaurant Two",
        owner_id=admin.id,
        address="Chennai Central",
        city="Chennai",
        phone="9876543211",
        cuisine_type="Chinese",
        opening_time=time(10, 0),
        closing_time=time(23, 0),
        delivery_radius=12.0,
        delivery_time=35,
    )

    db.add_all([
        restaurant_1,
        restaurant_2,
    ])

    db.commit()

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        "/admin-analytics/total-restaurants",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_restaurants"] == 2


# =========================================================
# STEP 2 - TOTAL CUSTOMERS
# =========================================================

def test_total_customers(
    client,
    db,
    admin,
):
    from app.models.customer import Customer

    customer_1 = Customer(
        name="Customer One",
        email="customer1@gmail.com",
        phone="9876543210",
    )

    customer_2 = Customer(
        name="Customer Two",
        email="customer2@gmail.com",
        phone="9876543211",
    )

    db.add_all([
        customer_1,
        customer_2,
    ])

    db.commit()

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        "/admin-analytics/total-customers",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_customers"] == 2


# =========================================================
# STEP 3 - TOTAL ORDERS
# =========================================================

def test_total_orders(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Order Customer",
        email="ordercustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Order Customer",
        email="ordercustomer@gmail.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Customer Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="123 Main Street",
        city="Chennai",
        pincode="600001",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Order Test Restaurant",
        owner_id=admin.id,
        address="456 Restaurant Street",
        city="Chennai",
        phone="9876543212",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Three Orders
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Total Orders API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/total-orders",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 3


# =========================================================
# STEP 4 - TOTAL REVENUE
# =========================================================

def test_total_revenue(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Revenue Customer",
        email="revenuecustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Revenue Customer",
        email="revenuecustomer@gmail.com",
        phone="9876543220",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Customer Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="789 Revenue Street",
        city="Chennai",
        pincode="600002",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Revenue Test Restaurant",
        owner_id=admin.id,
        address="789 Restaurant Street",
        city="Chennai",
        phone="9876543221",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Three Orders
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Total Revenue API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/total-revenue",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_revenue"] == 690.0


# =========================================================
# STEP 5 - TOTAL REFUNDS
# =========================================================

def test_total_refunds(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address
    from app.models.restaurant import Restaurant
    from app.models.payment import (
        Payment,
        PaymentMethod,
        PaymentStatus,
    )
    from app.models.refund import Refund

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Refund Customer",
        email="refundcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Refund Customer",
        email="refundcustomer@gmail.com",
        phone="9876543230",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="100 Refund Street",
        city="Chennai",
        pincode="600003",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Refund Test Restaurant",
        owner_id=admin.id,
        address="100 Restaurant Street",
        city="Chennai",
        phone="9876543231",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Order
    # ---------------------------------------------------------

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=25.0,
        total_amount=545.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # ---------------------------------------------------------
    # 6. Create Payment
    # ---------------------------------------------------------

    payment = Payment(
        order_id=order.id,
        amount=545.0,
        payment_method=PaymentMethod.UPI,
        transaction_id="REFUND-TXN-001",
        payment_status=PaymentStatus.REFUNDED,
        paid_at=datetime.utcnow(),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # ---------------------------------------------------------
    # 7. Create Refund
    # ---------------------------------------------------------

    refund = Refund(
        payment_id=payment.id,
        order_id=order.id,
        amount=545.0,
        refund_status="Success",
        reason="Order cancelled",
        refunded_at=datetime.utcnow(),
    )

    db.add(refund)
    db.commit()
    db.refresh(refund)

    # ---------------------------------------------------------
    # 8. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 9. Call Total Refunds API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/total-refunds",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 10. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_refunds"] == 545.0
    
# =========================================================
# STEP 6 - ACTIVE DELIVERY PARTNERS
# =========================================================

def test_active_delivery_partners(
    client,
    db,
    admin,
):
    from app.models.delivery_partner import (
        DeliveryPartner,
        DeliveryPartnerStatus,
    )

    # ---------------------------------------------------------
    # 1. Create Delivery Partners
    # ---------------------------------------------------------

    partner_1 = DeliveryPartner(
        name="Delivery Partner One",
        phone="9876500001",
        vehicle_type="Bike",
        vehicle_number="TN01AB1001",
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    partner_2 = DeliveryPartner(
        name="Delivery Partner Two",
        phone="9876500002",
        vehicle_type="Bike",
        vehicle_number="TN01AB1002",
        availability_status=DeliveryPartnerStatus.AVAILABLE,
        current_location="Chennai",
    )

    partner_3 = DeliveryPartner(
        name="Delivery Partner Three",
        phone="9876500003",
        vehicle_type="Car",
        vehicle_number="TN01AB1003",
        availability_status=DeliveryPartnerStatus.BUSY,
        current_location="Chennai",
    )

    partner_4 = DeliveryPartner(
        name="Delivery Partner Four",
        phone="9876500004",
        vehicle_type="Bike",
        vehicle_number="TN01AB1004",
        availability_status=DeliveryPartnerStatus.OFFLINE,
        current_location="Chennai",
    )

    db.add_all([
        partner_1,
        partner_2,
        partner_3,
        partner_4,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 2. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 3. Call Active Delivery Partners API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/active-delivery-partners",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 4. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["active_delivery_partners"] == 2
    
# =========================================================
# STEP 7 - TOP RESTAURANTS
# =========================================================

def test_top_restaurants(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Top Restaurant Customer",
        email="toprestaurantcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Top Restaurant Customer",
        email="toprestaurantcustomer@gmail.com",
        phone="9876543240",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Top Restaurant Street",
        city="Chennai",
        pincode="600004",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurants
    # ---------------------------------------------------------

    restaurant_1 = Restaurant(
        restaurant_name="Top Restaurant One",
        owner_id=admin.id,
        address="Restaurant One Street",
        city="Chennai",
        phone="9876543241",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    restaurant_2 = Restaurant(
        restaurant_name="Top Restaurant Two",
        owner_id=admin.id,
        address="Restaurant Two Street",
        city="Chennai",
        phone="9876543242",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    restaurant_3 = Restaurant(
        restaurant_name="Top Restaurant Three",
        owner_id=admin.id,
        address="Restaurant Three Street",
        city="Chennai",
        phone="9876543243",
        cuisine_type="Italian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add_all([
        restaurant_1,
        restaurant_2,
        restaurant_3,
    ])

    db.commit()

    db.refresh(restaurant_1)
    db.refresh(restaurant_2)
    db.refresh(restaurant_3)

    # ---------------------------------------------------------
    # 5. Create Delivered Orders
    #
    # Restaurant One  -> 3 delivered orders
    # Restaurant Two  -> 2 delivered orders
    # Restaurant Three -> 1 delivered order
    # ---------------------------------------------------------

    orders = [
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_1.id,
            address_id=address.id,
            subtotal=100.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=125.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_1.id,
            address_id=address.id,
            subtotal=150.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=175.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_1.id,
            address_id=address.id,
            subtotal=200.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=230.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_2.id,
            address_id=address.id,
            subtotal=120.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=145.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_2.id,
            address_id=address.id,
            subtotal=180.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=210.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=restaurant_3.id,
            address_id=address.id,
            subtotal=100.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=125.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
    ]

    db.add_all(orders)
    db.commit()

    # ---------------------------------------------------------
    # 6. Create Non-Delivered Order
    #
    # This should NOT affect restaurant ranking.
    # ---------------------------------------------------------

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant_3.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    db.add(pending_order)
    db.commit()

    # ---------------------------------------------------------
    # 7. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 8. Call Top Restaurants API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/top-restaurants",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 9. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "top_restaurants" in data

    assert len(data["top_restaurants"]) == 3

    assert data["top_restaurants"][0]["restaurant_id"] == restaurant_1.id
    assert data["top_restaurants"][0]["restaurant_name"] == "Top Restaurant One"
    assert data["top_restaurants"][0]["total_orders"] == 3

    assert data["top_restaurants"][1]["restaurant_id"] == restaurant_2.id
    assert data["top_restaurants"][1]["restaurant_name"] == "Top Restaurant Two"
    assert data["top_restaurants"][1]["total_orders"] == 2

    assert data["top_restaurants"][2]["restaurant_id"] == restaurant_3.id
    assert data["top_restaurants"][2]["restaurant_name"] == "Top Restaurant Three"
    assert data["top_restaurants"][2]["total_orders"] == 1
    
# =========================================================
# STEP 8 - TOP FOOD ITEMS
# =========================================================

def test_top_food_items(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus, OrderItem
    from app.models.user import User
    from app.models.customer import Customer, Address
    from app.models.menu import MenuItem

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Food Item Customer",
        email="fooditemcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Food Item Customer",
        email="fooditemcustomer@gmail.com",
        phone="9876543250",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Food Item Street",
        city="Chennai",
        pincode="600005",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Food Item Restaurant",
        owner_id=admin.id,
        address="Food Restaurant Street",
        city="Chennai",
        phone="9876543251",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Menu Items
    # ---------------------------------------------------------

    biryani = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Chicken Biryani",
        description="Chicken biryani",
        price=250.0,
        preparation_time=30,
        availability=True,
        vegetarian=False,
    )

    pizza = MenuItem(
        restaurant_id=restaurant.id,
        category="Main Course",
        name="Veg Pizza",
        description="Vegetable pizza",
        price=200.0,
        preparation_time=25,
        availability=True,
        vegetarian=True,
    )

    burger = MenuItem(
        restaurant_id=restaurant.id,
        category="Fast Food",
        name="Chicken Burger",
        description="Chicken burger",
        price=150.0,
        preparation_time=20,
        availability=True,
        vegetarian=False,
    )

    db.add_all([
        biryani,
        pizza,
        burger,
    ])

    db.commit()

    db.refresh(biryani)
    db.refresh(pizza)
    db.refresh(burger)

    # ---------------------------------------------------------
    # 6. Create Delivered Orders
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=650.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=30.0,
        total_amount=700.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=550.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=25.0,
        total_amount=595.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
    ])

    db.commit()

    db.refresh(order_1)
    db.refresh(order_2)
    db.refresh(order_3)

    # ---------------------------------------------------------
    # 7. Create Order Items
    #
    # Chicken Biryani -> 8
    # Veg Pizza       -> 5
    # Chicken Burger  -> 2
    # ---------------------------------------------------------

    items = [
        OrderItem(
            order_id=order_1.id,
            menu_item_id=biryani.id,
            quantity=3,
            unit_price=250.0,
            subtotal=750.0,
        ),
        OrderItem(
            order_id=order_1.id,
            menu_item_id=pizza.id,
            quantity=2,
            unit_price=200.0,
            subtotal=400.0,
        ),
        OrderItem(
            order_id=order_2.id,
            menu_item_id=biryani.id,
            quantity=5,
            unit_price=250.0,
            subtotal=1250.0,
        ),
        OrderItem(
            order_id=order_2.id,
            menu_item_id=pizza.id,
            quantity=3,
            unit_price=200.0,
            subtotal=600.0,
        ),
        OrderItem(
            order_id=order_3.id,
            menu_item_id=pizza.id,
            quantity=0,
            unit_price=200.0,
            subtotal=0.0,
        ),
        OrderItem(
            order_id=order_3.id,
            menu_item_id=burger.id,
            quantity=2,
            unit_price=150.0,
            subtotal=300.0,
        ),
    ]

    # Remove the zero-quantity item because quantity represents
    # actual ordered units.
    items = [
        item for item in items
        if item.quantity > 0
    ]

    db.add_all(items)
    db.commit()

    # ---------------------------------------------------------
    # 8. Create Pending Order
    #
    # This must NOT affect the ranking.
    # ---------------------------------------------------------

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=280.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    db.add(pending_order)
    db.commit()

    pending_item = OrderItem(
        order_id=pending_order.id,
        menu_item_id=burger.id,
        quantity=100,
        unit_price=150.0,
        subtotal=15000.0,
    )

    db.add(pending_item)
    db.commit()

    # ---------------------------------------------------------
    # 9. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 10. Call Top Food Items API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/top-food-items",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 11. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "top_food_items" in data

    assert len(data["top_food_items"]) == 3

    assert data["top_food_items"][0]["menu_item_id"] == biryani.id
    assert data["top_food_items"][0]["food_name"] == "Chicken Biryani"
    assert data["top_food_items"][0]["total_quantity"] == 8

    assert data["top_food_items"][1]["menu_item_id"] == pizza.id
    assert data["top_food_items"][1]["food_name"] == "Veg Pizza"
    assert data["top_food_items"][1]["total_quantity"] == 5

    assert data["top_food_items"][2]["menu_item_id"] == burger.id
    assert data["top_food_items"][2]["food_name"] == "Chicken Burger"
    assert data["top_food_items"][2]["total_quantity"] == 2
    
# =========================================================
# STEP 9 - MOST POPULAR CUISINE
# =========================================================

def test_most_popular_cuisine(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Cuisine Customer",
        email="cuisinecustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Cuisine Customer",
        email="cuisinecustomer@gmail.com",
        phone="9876543260",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Cuisine Street",
        city="Chennai",
        pincode="600006",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurants
    #
    # Indian  -> 4 delivered orders
    # Chinese -> 2 delivered orders
    # Italian -> 1 delivered order
    # ---------------------------------------------------------

    indian_restaurant = Restaurant(
        restaurant_name="Indian Cuisine Restaurant",
        owner_id=admin.id,
        address="Indian Restaurant Street",
        city="Chennai",
        phone="9876543261",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    chinese_restaurant = Restaurant(
        restaurant_name="Chinese Cuisine Restaurant",
        owner_id=admin.id,
        address="Chinese Restaurant Street",
        city="Chennai",
        phone="9876543262",
        cuisine_type="Chinese",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    italian_restaurant = Restaurant(
        restaurant_name="Italian Cuisine Restaurant",
        owner_id=admin.id,
        address="Italian Restaurant Street",
        city="Chennai",
        phone="9876543263",
        cuisine_type="Italian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add_all([
        indian_restaurant,
        chinese_restaurant,
        italian_restaurant,
    ])

    db.commit()

    db.refresh(indian_restaurant)
    db.refresh(chinese_restaurant)
    db.refresh(italian_restaurant)

    # ---------------------------------------------------------
    # 5. Create Delivered Orders
    # ---------------------------------------------------------

    delivered_orders = [
        # Indian - 4 orders
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=100.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=125.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=150.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=175.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=200.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=230.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=indian_restaurant.id,
            address_id=address.id,
            subtotal=250.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=280.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),

        # Chinese - 2 orders
        Order(
            customer_id=customer.id,
            restaurant_id=chinese_restaurant.id,
            address_id=address.id,
            subtotal=120.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=5.0,
            total_amount=145.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
        Order(
            customer_id=customer.id,
            restaurant_id=chinese_restaurant.id,
            address_id=address.id,
            subtotal=180.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=210.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),

        # Italian - 1 order
        Order(
            customer_id=customer.id,
            restaurant_id=italian_restaurant.id,
            address_id=address.id,
            subtotal=200.0,
            delivery_fee=20.0,
            discount=0.0,
            tax=10.0,
            total_amount=230.0,
            order_status=OrderStatus.DELIVERED,
            payment_status="Paid",
        ),
    ]

    db.add_all(delivered_orders)
    db.commit()

    # ---------------------------------------------------------
    # 6. Create Non-Delivered Orders
    #
    # These must NOT affect cuisine popularity.
    # ---------------------------------------------------------

    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=chinese_restaurant.id,
        address_id=address.id,
        subtotal=500.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=25.0,
        total_amount=545.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
    )

    cancelled_order = Order(
        customer_id=customer.id,
        restaurant_id=italian_restaurant.id,
        address_id=address.id,
        subtotal=600.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=30.0,
        total_amount=650.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
    )

    db.add_all([
        pending_order,
        cancelled_order,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 7. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 8. Call Most Popular Cuisine API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/most-popular-cuisine",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 9. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["cuisine_type"] == "Indian"
    assert data["total_orders"] == 4
    
# =========================================================
# STEP 10 - DAILY ORDERS
# =========================================================

def test_daily_orders(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Daily Orders Customer",
        email="dailyorderscustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Daily Orders Customer",
        email="dailyorderscustomer@gmail.com",
        phone="9876543270",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Daily Orders Street",
        city="Chennai",
        pincode="600007",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Daily Orders Restaurant",
        owner_id=admin.id,
        address="Daily Orders Restaurant Street",
        city="Chennai",
        phone="9876543271",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Orders
    #
    # 2026-09-10 -> 3 orders
    # 2026-09-11 -> 2 orders
    # 2026-09-12 -> 1 order
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.PENDING,
        payment_status="Pending",
        created_at=datetime(2026, 9, 10, 10, 0, 0),
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=150.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=175.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 10, 12, 0, 0),
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 10, 18, 0, 0),
    )

    order_4 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=120.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=145.0,
        order_status=OrderStatus.PREPARING,
        payment_status="Paid",
        created_at=datetime(2026, 9, 11, 11, 0, 0),
    )

    order_5 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=180.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=210.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
        created_at=datetime(2026, 9, 11, 19, 0, 0),
    )

    order_6 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=280.0,
        order_status=OrderStatus.OUT_FOR_DELIVERY,
        payment_status="Paid",
        created_at=datetime(2026, 9, 12, 15, 0, 0),
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
        order_4,
        order_5,
        order_6,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Daily Orders API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/daily-orders",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "daily_orders" in data

    assert len(data["daily_orders"]) == 3

    # ---------------------------------------------------------
    # 9. Verify 2026-09-10
    # ---------------------------------------------------------

    assert data["daily_orders"][0]["date"] == "2026-09-10"
    assert data["daily_orders"][0]["total_orders"] == 3

    # ---------------------------------------------------------
    # 10. Verify 2026-09-11
    # ---------------------------------------------------------

    assert data["daily_orders"][1]["date"] == "2026-09-11"
    assert data["daily_orders"][1]["total_orders"] == 2

    # ---------------------------------------------------------
    # 11. Verify 2026-09-12
    # ---------------------------------------------------------

    assert data["daily_orders"][2]["date"] == "2026-09-12"
    assert data["daily_orders"][2]["total_orders"] == 1
    
# =========================================================
# STEP 11 - MONTHLY REVENUE
# =========================================================

def test_monthly_revenue(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Monthly Revenue Customer",
        email="monthlyrevenuecustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Monthly Revenue Customer",
        email="monthlyrevenuecustomer@gmail.com",
        phone="9876543280",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Monthly Revenue Street",
        city="Chennai",
        pincode="600008",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Monthly Revenue Restaurant",
        owner_id=admin.id,
        address="Monthly Revenue Restaurant Street",
        city="Chennai",
        phone="9876543281",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Orders
    #
    # August 2026:
    # 100 + 200 + 300 = 600
    #
    # September 2026:
    # 400 + 500 = 900
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=80.0,
        delivery_fee=10.0,
        discount=0.0,
        tax=10.0,
        total_amount=100.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 8, 5, 10, 0, 0),
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=170.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=200.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 8, 15, 12, 0, 0),
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=30.0,
        discount=0.0,
        tax=20.0,
        total_amount=300.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 8, 25, 18, 0, 0),
    )

    order_4 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=350.0,
        delivery_fee=30.0,
        discount=0.0,
        tax=20.0,
        total_amount=400.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 5, 11, 0, 0),
    )

    order_5 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=450.0,
        delivery_fee=30.0,
        discount=0.0,
        tax=20.0,
        total_amount=500.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
        created_at=datetime(2026, 9, 15, 19, 0, 0),
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
        order_4,
        order_5,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Monthly Revenue API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/monthly-revenue",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert "monthly_revenue" in data

    assert len(data["monthly_revenue"]) == 2

    # ---------------------------------------------------------
    # 9. Verify August 2026
    # ---------------------------------------------------------

    assert data["monthly_revenue"][0]["month"] == "2026-08"
    assert data["monthly_revenue"][0]["total_revenue"] == 600.0

    # ---------------------------------------------------------
    # 10. Verify September 2026
    # ---------------------------------------------------------

    assert data["monthly_revenue"][1]["month"] == "2026-09"
    assert data["monthly_revenue"][1]["total_revenue"] == 900.0
    
# =========================================================
# STEP 12 - CANCELLATION RATE
# =========================================================

def test_cancellation_rate(
    client,
    db,
    admin,
):
    from app.models.order import Order, OrderStatus
    from app.models.user import User
    from app.models.customer import Customer, Address

    # ---------------------------------------------------------
    # 1. Create Customer User
    # ---------------------------------------------------------

    customer_user = User(
        name="Cancellation Customer",
        email="cancellationcustomer@gmail.com",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    # ---------------------------------------------------------
    # 2. Create Customer
    # ---------------------------------------------------------

    customer = Customer(
        user_id=customer_user.id,
        name="Cancellation Customer",
        email="cancellationcustomer@gmail.com",
        phone="9876543290",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # ---------------------------------------------------------
    # 3. Create Address
    # ---------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Cancellation Street",
        city="Chennai",
        pincode="600009",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # ---------------------------------------------------------
    # 4. Create Restaurant
    # ---------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Cancellation Test Restaurant",
        owner_id=admin.id,
        address="Cancellation Restaurant Street",
        city="Chennai",
        phone="9876543291",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        delivery_radius=10.0,
        delivery_time=30,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # ---------------------------------------------------------
    # 5. Create Five Orders
    #
    # Total Orders      = 5
    # Cancelled Orders  = 2
    #
    # Cancellation Rate = (2 / 5) * 100
    #                    = 40.0%
    # ---------------------------------------------------------

    order_1 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=125.0,
        order_status=OrderStatus.DELIVERED,
        payment_status="Paid",
    )

    order_2 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=150.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=5.0,
        total_amount=175.0,
        order_status=OrderStatus.ACCEPTED,
        payment_status="Paid",
    )

    order_3 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=200.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=230.0,
        order_status=OrderStatus.PREPARING,
        payment_status="Paid",
    )

    order_4 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=250.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=10.0,
        total_amount=280.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
    )

    order_5 = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=300.0,
        delivery_fee=20.0,
        discount=0.0,
        tax=15.0,
        total_amount=335.0,
        order_status=OrderStatus.CANCELLED,
        payment_status="Refunded",
    )

    db.add_all([
        order_1,
        order_2,
        order_3,
        order_4,
        order_5,
    ])

    db.commit()

    # ---------------------------------------------------------
    # 6. Create Admin Access Token
    # ---------------------------------------------------------

    token = create_access_token(
        user_id=admin.id,
        role=admin.role,
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ---------------------------------------------------------
    # 7. Call Cancellation Rate API
    # ---------------------------------------------------------

    response = client.get(
        "/admin-analytics/cancellation-rate",
        headers=headers,
    )

    # ---------------------------------------------------------
    # 8. Verify Response
    # ---------------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 5

    assert data["cancelled_orders"] == 2

    assert data["cancellation_rate"] == 40.0