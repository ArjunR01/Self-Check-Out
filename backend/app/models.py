from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class CartStatus(str, Enum):
    active = "active"
    checkedout = "checkedout"


class InvoiceStatus(str, Enum):
    pending = "pending"
    paid = "paid"


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    carts = relationship("Cart", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")


class StoreOfficial(Base):
    __tablename__ = "store_officials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="cashier")  # e.g., admin, cashier
    created_at = Column(DateTime, default=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="official")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    code = Column(String, unique=True, index=True, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    weight_per_unit = Column(Float, nullable=False)
    available_qty = Column(Integer, nullable=False, default=0)

    cart_items = relationship("CartItem", back_populates="product")


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(SAEnum(CartStatus), default=CartStatus.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="cart", uselist=False)


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False, default=0.0)
    net_weight = Column(Float, nullable=False, default=0.0)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
    )


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    # Using existing 'code' column as QR code string to avoid breaking existing DBs.
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., INV-<uuid>
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    official_id = Column(Integer, ForeignKey("store_officials.id"), nullable=True)
    total = Column(Float, nullable=False, default=0.0)
    date = Column(DateTime, default=datetime.utcnow)  # creation timestamp
    status = Column(SAEnum(InvoiceStatus), default=InvoiceStatus.pending, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="invoices")
    cart = relationship("Cart", back_populates="invoice")
    official = relationship("StoreOfficial", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False, default=0.0)
    net_weight = Column(Float, nullable=False, default=0.0)

    invoice = relationship("Invoice", back_populates="items")
    # product relationship optional; not strictly needed for lookups
    product = relationship("Product")

