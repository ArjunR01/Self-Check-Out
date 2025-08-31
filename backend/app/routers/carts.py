from uuid import uuid4
from base64 import b64encode
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..schemas import ItemInput
from ..dependencies import get_current_customer
from ..utils.qr import generate_qr_png

router = APIRouter(prefix="/carts", tags=["carts"])


class AttachRequestModel:
    items: List[ItemInput]


def _get_or_create_active_cart(db: Session, customer_id: int) -> models.Cart:
    cart = (
        db.query(models.Cart)
        .filter(models.Cart.customer_id == customer_id, models.Cart.status == models.CartStatus.active)
        .first()
    )
    if not cart:
        cart = models.Cart(customer_id=customer_id, status=models.CartStatus.active)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("/attach")
def attach_cart(payload: dict, customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    items_payload = payload.get("items", [])
    if not items_payload:
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart = _get_or_create_active_cart(db, customer.id)

    # Clear existing items
    for it in list(cart.items):
        db.delete(it)
    db.flush()

    # Add items by product code, dedupe by code and sum quantities
    merged: dict[str, int] = {}
    for item in items_payload:
        code = item.get("code")
        qty = int(item.get("quantity", 1))
        if not code:
            raise HTTPException(status_code=400, detail="Invalid item payload: missing code")
        if qty <= 0:
            continue
        merged[code] = merged.get(code, 0) + qty

    for code, qty in merged.items():
        product = db.query(models.Product).filter(models.Product.code == code).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Invalid product — not available in this store")
        ci = models.CartItem(cart_id=cart.id, product_id=product.id, quantity=qty)
        db.add(ci)
        db.flush()
        # compute subtotal and net weight
        ci.subtotal = product.price_per_unit * ci.quantity
        ci.net_weight = product.weight_per_unit * ci.quantity

    db.commit()
    db.refresh(cart)

    total = sum(i.subtotal for i in cart.items)
    total_weight = sum(i.net_weight for i in cart.items)

    return {
        "cart_id": cart.id,
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "product_name": i.product.name,
                "quantity": i.quantity,
                "subtotal": i.subtotal,
                "net_weight": i.net_weight,
            }
            for i in cart.items
        ],
        "total": total,
        "total_weight": total_weight,
    }


@router.post("/{cart_id}/checkout")
def checkout_cart(cart_id: int, customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    cart = db.query(models.Cart).filter(models.Cart.id == cart_id).first()
    if not cart or cart.customer_id != customer.id or cart.status != models.CartStatus.active:
        raise HTTPException(status_code=404, detail="Cart not found or not active")

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Stock validation
    for item in cart.items:
        product = item.product
        if item.quantity > product.available_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.available_qty}",
            )

    # Create invoice code and invoice
    inv_code = f"INV-{uuid4().hex[:12].upper()}"
    total = sum(i.subtotal for i in cart.items)
    total_weight = sum(i.net_weight for i in cart.items)

    invoice = models.Invoice(
        code=inv_code,
        customer_id=customer.id,
        cart_id=cart.id,
        total=total,
        status=models.InvoiceStatus.pending,
    )
    db.add(invoice)
    db.flush()
    db.refresh(invoice)

    # Snapshot items into invoice_items to prevent later drift
    for item in cart.items:
        inv_item = models.InvoiceItem(
            invoice_id=invoice.id,
            product_id=item.product_id,
            quantity=item.quantity,
            subtotal=item.subtotal,
            net_weight=item.net_weight,
        )
        db.add(inv_item)

    cart.status = models.CartStatus.checkedout
    db.commit()
    db.refresh(invoice)

    # Generate QR image (base64)
    png_bytes = generate_qr_png(inv_code)
    qr_b64 = b64encode(png_bytes).decode("utf-8")

    return {
        "invoice_id": invoice.id,
        "qr_code": inv_code,
        "qr_base64": qr_b64,
        "total": total,
        "total_net_weight": total_weight,
    }

