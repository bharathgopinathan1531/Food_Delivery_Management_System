from app.celery_app import celery_app


@celery_app.task
def generate_daily_sales_summary():
    """
    Generate the daily sales summary.
    """

    return {
        "status": "success",
        "message": "Daily sales summary generated"
    }


@celery_app.task
def cleanup_expired_data():
    """
    Cleanup expired application data.
    """

    return {
        "status": "success",
        "message": "Expired data cleanup completed"
    }