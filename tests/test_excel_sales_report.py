from io import BytesIO

from openpyxl import load_workbook

from app.services.sales_report_service import generate_sales_report


def test_generate_sales_report():
    sales_data = [
        {
            "order_id": 101,
            "customer": "Bharath",
            "total_amount": 599.50,
        },
        {
            "order_id": 102,
            "customer": "Test Customer",
            "total_amount": 250.00,
        },
    ]

    report = generate_sales_report(
        sales_data
    )

    assert isinstance(report, BytesIO)

    content = report.getvalue()

    assert len(content) > 100


def test_sales_report_contains_data():
    sales_data = [
        {
            "order_id": 201,
            "customer": "Bharath",
            "total_amount": 750.00,
        }
    ]

    report = generate_sales_report(
        sales_data
    )

    workbook = load_workbook(report)

    worksheet = workbook["Sales Report"]

    assert worksheet["A1"].value == "Order ID"
    assert worksheet["B1"].value == "Customer"
    assert worksheet["C1"].value == "Total Amount"

    assert worksheet["A2"].value == 201
    assert worksheet["B2"].value == "Bharath"
    assert worksheet["C2"].value == 750.00