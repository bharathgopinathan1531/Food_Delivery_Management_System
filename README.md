# Food Delivery Management Platform

A production-oriented **Food Delivery Management Platform** built with **FastAPI, Python, SQLAlchemy, SQLite/PostgreSQL, JWT Authentication, Redis, Celery, WebSockets, Docker, and Pytest**.

The platform provides secure, scalable APIs for managing customers, restaurants, menu items, carts, orders, delivery partners, payments, refunds, reviews, order tracking, analytics, and audit logs.

---

## 📌 Project Overview

The Food Delivery Management Platform is designed as a modular backend system that supports the complete food-ordering workflow.

It provides:

- Secure authentication and authorization
- Role-based access control
- Restaurant and menu management
- Customer and address management
- Cart management
- Coupon management
- Order processing
- Delivery partner management
- Real-time order tracking
- Payment and refund management
- Restaurant dashboard
- Admin analytics
- Audit logging
- Soft delete
- Redis caching
- PDF invoice generation
- Excel sales reports
- Celery background and scheduled tasks
- Docker and Docker Compose support
- API versioning
- Unit and integration testing

---

## 🚀 Key Features

### Authentication & Authorization

- User registration
- User login
- JWT access tokens
- Refresh token support
- Password hashing
- Role-based authorization
- Protected API endpoints

### User Roles

The system supports the following roles:

- Admin
- Restaurant Owner
- Restaurant Staff
- Delivery Partner
- Customer

---

## 🍽️ Restaurant Management

- Create restaurants
- Update restaurant details
- Delete restaurants
- Restaurant status management
- Restaurant owner authorization
- Restaurant staff management

---

## 📋 Menu Management

- Create menu items
- Update menu items
- Delete menu items
- Menu item availability
- Restaurant-specific menu management

---

## 👤 Customer Management

- Customer registration
- Customer profile management
- Address management
- Customer-specific data access

---

## 🛒 Cart Management

- Create cart
- Add items to cart
- Update cart items
- Remove cart items
- Cart total calculation

---

## 🎟️ Coupon Management

- Coupon creation
- Coupon validation
- Discount handling
- Coupon application to orders

---

## 📦 Order Management

- Create orders
- Order status management
- Order item management
- Order total calculation
- Delivery partner assignment
- Order cancellation
- Order history

### Order Status

```text
Pending
Accepted
Preparing
Ready
Picked Up
Out for Delivery
Delivered
Cancelled

Food_Delivery_Management_System/
│
├── app/
│   ├── cache/
│   │   ├── __init__.py
│   │   └── redis_client.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   │
│   ├── celery_app.py
│   ├── websocket_manager.py
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_database_configuration.py
│   ├── test_database_indexes.py
│   ├── test_efficient_joins.py
│   ├── test_transaction_management.py
│   ├── test_session_handling.py
│   ├── test_n_plus_one_queries.py
│   ├── test_redis_cache.py
│   ├── test_websocket_order_tracking.py
│   ├── test_location_service.py
│   ├── test_pdf_invoice.py
│   ├── test_excel_sales_report.py
│   ├── test_celery_tasks.py
│   ├── test_unit_sales_report.py
│   ├── test_integration_api.py
│   └── test_api_versioning.py
│
├── .github/
│   └── workflows/
│
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

👨‍💻 Author
Bharath G
Food Delivery Management Platform
Backend Development Project