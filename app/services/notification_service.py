import logging
from datetime import datetime, timezone


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger("food_delivery.notifications")


# ============================================================
# NOTIFICATION SERVICE
# ============================================================

def send_notification(
    notification_type: str,
    recipient_id: int,
    message: str,
):
    """
    Background notification task.

    This function is intentionally independent from the API
    request lifecycle so FastAPI BackgroundTasks can execute it
    after the response has been sent.
    """

    notification = {
        "notification_type": notification_type,
        "recipient_id": recipient_id,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Notification sent: %s",
        notification,
    )

    return notification


# ============================================================
# ORDER NOTIFICATIONS
# ============================================================

def notify_order_placed(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Order Placed",
        recipient_id=recipient_id,
        message=f"Your order #{order_id} has been placed successfully.",
    )


def notify_order_accepted(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Order Accepted",
        recipient_id=recipient_id,
        message=f"Your order #{order_id} has been accepted by the restaurant.",
    )


def notify_food_ready(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Food Ready",
        recipient_id=recipient_id,
        message=f"Your food for order #{order_id} is ready.",
    )


def notify_driver_assigned(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Driver Assigned",
        recipient_id=recipient_id,
        message=f"A delivery partner has been assigned to order #{order_id}.",
    )


def notify_out_for_delivery(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Out for Delivery",
        recipient_id=recipient_id,
        message=f"Your order #{order_id} is out for delivery.",
    )


def notify_order_delivered(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Order Delivered",
        recipient_id=recipient_id,
        message=f"Your order #{order_id} has been delivered successfully.",
    )


# ============================================================
# PAYMENT NOTIFICATIONS
# ============================================================

def notify_payment_success(
    recipient_id: int,
    order_id: int,
):
    return send_notification(
        notification_type="Payment Success",
        recipient_id=recipient_id,
        message=f"Payment for order #{order_id} was successful.",
    )


# ============================================================
# REFUND NOTIFICATIONS
# ============================================================

def notify_refund_processed(
    recipient_id: int,
    order_id: int,
    amount: float,
):
    return send_notification(
        notification_type="Refund Processed",
        recipient_id=recipient_id,
        message=(
            f"Refund of {amount:.2f} for order "
            f"#{order_id} has been processed successfully."
        ),
    )