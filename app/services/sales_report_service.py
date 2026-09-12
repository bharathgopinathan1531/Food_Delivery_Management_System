from io import BytesIO

from openpyxl import Workbook


def generate_sales_report(
    sales_data: list[dict],
) -> BytesIO:
    """
    Generate an Excel sales report.
    """

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Sales Report"

    headers = [
        "Order ID",
        "Customer",
        "Total Amount",
    ]

    worksheet.append(headers)

    for sale in sales_data:
        worksheet.append([
            sale["order_id"],
            sale["customer"],
            sale["total_amount"],
        ])

    buffer = BytesIO()

    workbook.save(buffer)

    buffer.seek(0)

    return buffer