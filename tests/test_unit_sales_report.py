from app.services.sales_report_service import generate_sales_report


def test_sales_report_unit():
    sales_data = [
        {
            "order_id": 1,
            "customer": "Bharath",
            "total_amount": 500.00,
        }
    ]

    report = generate_sales_report(sales_data)

    assert report is not None
    assert len(report.getvalue()) > 0