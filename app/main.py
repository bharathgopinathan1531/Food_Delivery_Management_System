from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    User,
    Restaurant,
    MenuItem,
    RestaurantStaff,
    Customer,
    Address,
    Cart,
    CartItem,
)

from app.routes.auth import router as auth_router
from app.routes.restaurants import router as restaurant_router
from app.routes.menu import router as menu_router
from app.routes.customers import (
    router as customer_router,
    address_router,
)
from app.routes.cart import router as cart_router
from app.routes.coupons import router as coupon_router
from app.routes.orders import router as order_router
from app.routes.delivery_partners import (
    router as delivery_partner_router
)
from app.routes.order_tracking import (
    router as order_tracking_router
)
from app.routes.payments import router as payment_router
from app.routes.refunds import router as refunds_router
from app.routes.reviews import router as review_router

from app.routes.restaurant_dashboard import (
    router as restaurant_dashboard_router
)

from app.routes.admin_analytics import (
    router as admin_analytics_router
)

from app.routes.audit_logs import (
    router as audit_log_router
)


app = FastAPI(
    title="Food Delivery Management Platform",
    description="Food Delivery Management Platform API",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        }
    )


# ============================================================
# API VERSION 1 ROUTER
# ============================================================

api_v1_router = APIRouter(
    prefix="/api/v1"
)


# ============================================================
# VERSION 1 ROUTERS
# ============================================================

api_v1_router.include_router(auth_router)
api_v1_router.include_router(restaurant_router)
api_v1_router.include_router(menu_router)
api_v1_router.include_router(customer_router)
api_v1_router.include_router(address_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(coupon_router)
api_v1_router.include_router(order_router)
api_v1_router.include_router(delivery_partner_router)
api_v1_router.include_router(order_tracking_router)
api_v1_router.include_router(payment_router)
api_v1_router.include_router(refunds_router)
api_v1_router.include_router(review_router)
api_v1_router.include_router(
    restaurant_dashboard_router
)
api_v1_router.include_router(
    admin_analytics_router
)
api_v1_router.include_router(
    audit_log_router
)


# ============================================================
# VERSIONED API
# ============================================================

app.include_router(
    api_v1_router
)


# ============================================================
# LEGACY ROUTERS
# ============================================================
# Existing endpoints are preserved so previous tests
# and existing clients continue to work.

app.include_router(auth_router)
app.include_router(restaurant_router)
app.include_router(menu_router)
app.include_router(customer_router)
app.include_router(address_router)
app.include_router(cart_router)
app.include_router(coupon_router)
app.include_router(order_router)
app.include_router(delivery_partner_router)
app.include_router(order_tracking_router)
app.include_router(payment_router)
app.include_router(refunds_router)
app.include_router(review_router)
app.include_router(restaurant_dashboard_router)
app.include_router(admin_analytics_router)
app.include_router(audit_log_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Food Delivery Management Platform API",
        "version": "1.0.0",
        "level": 7,
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }