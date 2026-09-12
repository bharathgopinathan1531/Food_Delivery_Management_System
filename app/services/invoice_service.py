from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_invoice_pdf(
    order_id: int,
    customer_name: str,
    total_amount: float,
) -> BytesIO:
    """
    Generate a simple PDF invoice for an order.
    """

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    pdf.setTitle(
        f"Invoice-{order_id}"
    )

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawString(
        50,
        800,
        "Food Delivery Invoice"
    )

    pdf.setFont(
        "Helvetica",
        12
    )

    pdf.drawString(
        50,
        760,
        f"Order ID: {order_id}"
    )

    pdf.drawString(
        50,
        735,
        f"Customer: {customer_name}"
    )

    pdf.drawString(
        50,
        710,
        f"Total Amount: ₹{total_amount:.2f}"
    )

    pdf.drawString(
        50,
        660,
        "Thank you for ordering with us!"
    )

    pdf.save()

    buffer.seek(0)

    return buffer