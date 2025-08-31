from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models
from ..database import get_db
from ..dependencies import get_current_official, get_current_customer
from ..schemas import InvoiceOut, InvoiceDetailOut, CartItemOut
from ..utils.pdf import build_invoice_pdf
from ..utils.qr import generate_qr_png
from ..utils.mailer import send_invoice_email_if_enabled

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _items_out_for_invoice(invoice: models.Invoice) -> List[CartItemOut]:
    # Prefer immutable invoice_items snapshot if present; fallback to cart items for legacy invoices
    items_src = invoice.items if getattr(invoice, "items", None) else invoice.cart.items
    out: List[CartItemOut] = []
    for i in items_src:
        name = i.product.name if getattr(i, "product", None) else "Item"
        out.append(
            CartItemOut(
                id=i.id,
                product_id=i.product_id,
                product_name=name,
                quantity=i.quantity,
                subtotal=i.subtotal,
                net_weight=i.net_weight,
            )
        )
    return out


@router.get("/by-code/{code}", response_model=InvoiceDetailOut)
def get_invoice_by_code(code: str, db: Session = Depends(get_db), official: models.StoreOfficial = Depends(get_current_official)):
    invoice = db.query(models.Invoice).filter(models.Invoice.code == code).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    items = _items_out_for_invoice(invoice)
    # Compute total weight from invoice items if available
    src_items = invoice.items if getattr(invoice, "items", None) else invoice.cart.items
    total_weight = sum(i.net_weight for i in src_items)
    return InvoiceDetailOut(
            id=invoice.id,
            code=invoice.code,
            customer_id=invoice.customer_id,
            cart_id=invoice.cart_id,
            total=invoice.total,
            date=invoice.date,
            status=invoice.status.value,
            items=items,
            customer_name=invoice.customer.name,
            total_weight=total_weight,
        )


@router.post("/{id}/pay", response_model=InvoiceOut)
def pay_invoice(id: int, db: Session = Depends(get_db), official: models.StoreOfficial = Depends(get_current_official)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == models.InvoiceStatus.paid:
        raise HTTPException(status_code=400, detail="Invoice already paid")

    # Mark as paid and set metadata
    invoice.status = models.InvoiceStatus.paid
    invoice.official_id = official.id
    invoice.paid_at = datetime.utcnow()

    # Decrement inventory on payment
    for item in (invoice.items or []):
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.available_qty = max(0, product.available_qty - item.quantity)

    db.commit()
    db.refresh(invoice)

    # Email invoice (optional)
    try:
        pdf_bytes = build_invoice_pdf(invoice)
        send_invoice_email_if_enabled(invoice.customer.email, pdf_bytes, invoice.code)
    except Exception:
        # do not block payment on email errors
        pass

    return InvoiceOut(
        id=invoice.id,
        code=invoice.code,
        customer_id=invoice.customer_id,
        cart_id=invoice.cart_id,
        total=invoice.total,
        date=invoice.date,
        status=invoice.status.value,
    )


# Legacy: mark paid by code
@router.post("/{code}/mark_paid", response_model=InvoiceOut)
def mark_paid(code: str, db: Session = Depends(get_db), official: models.StoreOfficial = Depends(get_current_official)):
    invoice = db.query(models.Invoice).filter(models.Invoice.code == code).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == models.InvoiceStatus.paid:
        return InvoiceOut(
            id=invoice.id,
            code=invoice.code,
            customer_id=invoice.customer_id,
            cart_id=invoice.cart_id,
            total=invoice.total,
            date=invoice.date,
            status=invoice.status.value,
        )
    invoice.status = models.InvoiceStatus.paid
    invoice.official_id = official.id
    db.commit()
    db.refresh(invoice)

    # Email invoice (optional)
    try:
        pdf_bytes = build_invoice_pdf(invoice)
        send_invoice_email_if_enabled(invoice.customer.email, pdf_bytes, invoice.code)
    except Exception:
        # do not block payment on email errors
        pass

    return InvoiceOut(
        id=invoice.id,
        code=invoice.code,
        customer_id=invoice.customer_id,
        cart_id=invoice.cart_id,
        total=invoice.total,
        date=invoice.date,
        status=invoice.status.value,
    )


@router.get("/{id}/pdf")
def download_invoice_pdf_by_id(id: int, db: Session = Depends(get_db), customer: models.Customer = Depends(get_current_customer)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.customer_id != customer.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this invoice")
    pdf = build_invoice_pdf(invoice)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{invoice.code}.pdf"})


@router.get("/{code}/pdf")
def download_invoice_pdf(code: str, db: Session = Depends(get_db), customer: models.Customer = Depends(get_current_customer)):
    invoice = db.query(models.Invoice).filter(models.Invoice.code == code).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.customer_id != customer.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this invoice")
    pdf = build_invoice_pdf(invoice)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{code}.pdf"})


@router.get("/{id}/qr")
def get_invoice_qr_by_id(id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    png_bytes = generate_qr_png(invoice.code)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{code}/qr")
def get_invoice_qr(code: str, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.code == code).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    png_bytes = generate_qr_png(code)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/me/history", response_model=list[InvoiceOut])
def my_invoices(db: Session = Depends(get_db), customer: models.Customer = Depends(get_current_customer)):
    invoices = db.query(models.Invoice).filter(models.Invoice.customer_id == customer.id).order_by(models.Invoice.date.desc()).all()
    return [
        InvoiceOut(
            id=i.id,
            code=i.code,
            customer_id=i.customer_id,
            cart_id=i.cart_id,
            total=i.total,
            date=i.date,
            status=i.status.value,
        )
        for i in invoices
    ]

