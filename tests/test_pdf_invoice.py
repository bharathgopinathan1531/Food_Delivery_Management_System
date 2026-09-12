from io import BytesIO

from app.services.invoice_service import generate_invoice_pdf


def test_generate_invoice_pdf():
    pdf = generate_invoice_pdf(
        order_id=101,
        customer_name="Bharath",
        total_amount=599.50,
    )

    assert isinstance(pdf, BytesIO)

    content = pdf.getvalue()

    assert content.startswith(b"%PDF")
    assert len(content) > 100


def test_invoice_pdf_contains_data():
    pdf = generate_invoice_pdf(
        order_id=202,
        customer_name="Test Customer",
        total_amount=250.00,
    )

    content = pdf.getvalue()

    assert content.startswith(b"%PDF")
    assert len(content) > 0