from app.celery_app import celery_app
from app.tasks import (
    generate_daily_sales_summary,
    cleanup_expired_data,
)


def test_celery_app_configuration():
    assert celery_app.main == "food_delivery"
    assert celery_app.conf.timezone == "Asia/Kolkata"


def test_daily_sales_summary_task():
    result = generate_daily_sales_summary.apply(
        args=[]
    ).get()

    assert result["status"] == "success"
    assert "Daily sales summary" in result["message"]


def test_cleanup_expired_data_task():
    result = cleanup_expired_data.apply(
        args=[]
    ).get()

    assert result["status"] == "success"
    assert "cleanup" in result["message"].lower()