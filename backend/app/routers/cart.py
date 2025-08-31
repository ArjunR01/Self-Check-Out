from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models
from ..schemas import CartOut, CartItemOut, ScanRequest, UpdateQuantityRequest, InvoiceOut, FinalizeFromItemsRequest
from ..dependencies import get_current_customer

router = APIRouter(prefix="/cart", tags=["cart"])


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


def _recalc_item(item: models.CartItem):
    p = item.product
    item.subtotal = p.price_per_unit * item.quantity
    item.net_weight = p.weight_per_unit * item.quantity


def _cart_totals(cart: models.Cart):
    total = sum(i.subtotal for i in cart.items)
    total_weight = sum(i.net_weight for i in cart.items)
    return total, total_weight


def _cart_to_out(cart: models.Cart) -> CartOut:
    items_out: List[CartItemOut] = []
    for i in cart.items:
        items_out.append(
            CartItemOut(
                id=i.id,
                product_id=i.product_id,
                product_name=i.product.name,
                quantity=i.quantity,
                subtotal=i.subtotal,
                net_weight=i.net_weight,
            )
        )
    total, total_weight = _cart_totals(cart)
    return CartOut(id=cart.id, items=items_out, total=total, total_weight=total_weight)


@router.get("/", response_model=CartOut)
def get_cart(customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    cart = _get_or_create_active_cart(db, customer.id)
    # ensure calculations are correct
    for item in cart.items:
        _recalc_item(item)
    db.commit()
    db.refresh(cart)
    return _cart_to_out(cart)


@router.post("/scan", response_model=CartOut)
def scan_product(payload: ScanRequest, customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail="Invalid Product")

    cart = _get_or_create_active_cart(db, customer.id)
    item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == product.id).first()

    if item:
        item.quantity += max(1, payload.quantity)
    else:
        item = models.CartItem(cart_id=cart.id, product_id=product.id, quantity=max(1, payload.quantity))
        db.add(item)

    db.flush()
    db.refresh(item)

    _recalc_item(item)
    db.commit()
    db.refresh(cart)

    return _cart_to_out(cart)


@router.post("/update", response_model=CartOut)
def update_quantity(payload: UpdateQuantityRequest, customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    cart = _get_or_create_active_cart(db, customer.id)
    item = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == payload.product_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    if payload.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = payload.quantity
        _recalc_item(item)
    db.commit()
    db.refresh(cart)
    return _cart_to_out(cart)


@router.post("/finalize", response_model=InvoiceOut)
def finalize_cart(customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    cart = _get_or_create_active_cart(db, customer.id)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    # calculate totals and create invoice
    total, total_weight = _cart_totals(cart)
    code = str(uuid4())
    invoice = models.Invoice(
        code=code,
        customer_id=customer.id,
        cart_id=cart.id,
        total=total,
        status=models.InvoiceStatus.pending,
    )
    db.add(invoice)
    cart.status = models.CartStatus.checkedout
    db.commit()
    db.refresh(invoice)
    return InvoiceOut(
        id=invoice.id,
        code=invoice.code,
        customer_id=invoice.customer_id,
        cart_id=invoice.cart_id,
        total=invoice.total,
        date=invoice.date,
        status=invoice.status.value,
        total_weight=total_weight,
    )


@router.post("/finalize-from-items", response_model=InvoiceOut)
def finalize_from_items(payload: FinalizeFromItemsRequest, customer: models.Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # create a new cart for this checkout
    cart = models.Cart(customer_id=customer.id, status=models.CartStatus.active)
    db.add(cart)
    db.flush()
    db.refresh(cart)

    # add items by code
    for item in payload.items:
        product = db.query(models.Product).filter(models.Product.code == item.code).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Invalid Product: {item.code}")
        cart_item = models.CartItem(cart_id=cart.id, product_id=product.id, quantity=max(1, item.quantity))
        db.add(cart_item)
        db.flush()
        db.refresh(cart_item)
        _recalc_item(cart_item)

    # finalize
    db.flush()
    db.refresh(cart)
    total, total_weight = _cart_totals(cart)

    code = str(uuid4())
    invoice = models.Invoice(
        code=code,
        customer_id=customer.id,
        cart_id=cart.id,
        total=total,
        status=models.InvoiceStatus.pending,
    )
    db.add(invoice)
    cart.status = models.CartStatus.checkedout
    db.commit()
    db.refresh(invoice)

    return InvoiceOut(
        id=invoice.id,
        code=invoice.code,
        customer_id=invoice.customer_id,
        cart_id=invoice.cart_id,
        total=invoice.total,
        date=invoice.date,
        status=invoice.status.value,
        total_weight=total_weight,
    )

