from sqlalchemy import inspect

from app.database import Base
from app.models import (
    User,
    Restaurant,
    MenuItem,
    Customer,
    Address,
    Cart,
    CartItem,
    Order,
    OrderItem,
)


def test_sqlalchemy_models_are_registered():
    tables = Base.metadata.tables

    assert "users" in tables
    assert "restaurants" in tables
    assert "menu_items" in tables
    assert "customers" in tables
    assert "addresses" in tables
    assert "carts" in tables
    assert "cart_items" in tables
    assert "orders" in tables
    assert "order_items" in tables


def test_sqlalchemy_primary_keys_exist():
    assert User.__table__.primary_key.columns
    assert Restaurant.__table__.primary_key.columns
    assert MenuItem.__table__.primary_key.columns
    assert Customer.__table__.primary_key.columns
    assert Order.__table__.primary_key.columns


def test_sqlalchemy_foreign_keys_exist():
    restaurant_fks = {
        fk.target_fullname
        for fk in Restaurant.__table__.foreign_keys
    }

    menu_fks = {
        fk.target_fullname
        for fk in MenuItem.__table__.foreign_keys
    }

    customer_fks = {
        fk.target_fullname
        for fk in Customer.__table__.foreign_keys
    }

    order_fks = {
        fk.target_fullname
        for fk in Order.__table__.foreign_keys
    }

    assert "users.id" in restaurant_fks
    assert "restaurants.id" in menu_fks
    assert "users.id" in customer_fks
    assert "customers.id" in order_fks
    assert "restaurants.id" in order_fks


def test_sqlalchemy_relationships_exist():
    assert hasattr(User, "restaurants")
    assert hasattr(Restaurant, "owner")
    assert hasattr(Restaurant, "menu_items")
    assert hasattr(Customer, "addresses")
    assert hasattr(Cart, "items")
    assert hasattr(Order, "items")


def test_sqlalchemy_tables_have_inspection_support():
    mapper = inspect(Restaurant)

    assert mapper.local_table.name == "restaurants"
    assert mapper.primary_key
    assert mapper.relationships