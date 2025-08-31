from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models
from ..schemas import ProductCreate, ProductOut
from ..dependencies import get_current_official

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return products


@router.get("/by-id/{product_id}", response_model=ProductOut)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{code}", response_model=ProductOut)
def get_product_by_code_public(code: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.code == code).first()
    if not product:
        # Exact message per spec
        raise HTTPException(status_code=404, detail="Invalid product — not available in this store")
    return product


@router.get("/by-code/{code}", response_model=ProductOut)
def get_product_by_code(code: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.code == code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: models.StoreOfficial = Depends(get_current_official)):
    existing = db.query(models.Product).filter(models.Product.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product code already exists")
    product = models.Product(
        name=payload.name,
        description=payload.description,
        code=payload.code,
        price_per_unit=payload.price_per_unit,
        weight_per_unit=payload.weight_per_unit,
        available_qty=payload.available_qty,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

