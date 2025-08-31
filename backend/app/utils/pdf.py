from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from datetime import timezone

from .. import models


INR_SYMBOL = "₹"


def inr(amount: float) -> str:
    return f"{INR_SYMBOL}{amount:,.2f}"


def build_invoice_pdf(invoice: models.Invoice) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 20 * mm, "Store Invoice")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 28 * mm, f"Invoice Code: {invoice.code}")
    # Note: Using naive datetime as stored; display as-is. See README for IST notes.
    c.drawString(20 * mm, height - 34 * mm, f"Date: {invoice.date.strftime('%Y-%m-%d %H:%M')}")
    c.drawString(20 * mm, height - 40 * mm, f"Customer: {invoice.customer.name} ({invoice.customer.email})")

    # Table of items
    data = [["Product", "Qty", "Subtotal", "Net Wt"]]
    # Prefer invoice.items if present, else fall back to cart.items for legacy invoices
    line_items = invoice.items if getattr(invoice, "items", None) else invoice.cart.items
    total_weight = 0.0
    for item in line_items:
        name = item.product.name if getattr(item, "product", None) else "Item"
        qty = item.quantity
        subtotal = item.subtotal
        net_wt = item.net_weight
        total_weight += net_wt
        data.append([
            name,
            str(qty),
            inr(subtotal),
            f"{net_wt:.3f} kg",
        ])

    table = Table(data, colWidths=[90 * mm, 20 * mm, 35 * mm, 35 * mm])
    style = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ])
    table.setStyle(style)
    table.wrapOn(c, width - 40 * mm, height - 120 * mm)
    table.drawOn(c, 20 * mm, height - 110 * mm)

    # Totals & summary
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 20 * mm, 40 * mm, f"Total: {inr(invoice.total)}")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 20 * mm, 34 * mm, f"Total Net Weight: {total_weight:.3f} kg")

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

