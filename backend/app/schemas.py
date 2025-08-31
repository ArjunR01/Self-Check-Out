from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None


class OfficialCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "cashier"


class OfficialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    code: str
    price_per_unit: float
    weight_per_unit: float
    available_qty: int


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    code: str
    price_per_unit: float
    weight_per_unit: float
    available_qty: int


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    product_name: str
    quantity: int
    subtotal: float
    net_weight: float


class CartOut(BaseModel):
    id: int
    items: List[CartItemOut]
    total: float
    total_weight: float


class ScanRequest(BaseModel):
    product_id: int
    quantity: int = 1


class UpdateQuantityRequest(BaseModel):
    product_id: int
    quantity: int


class ItemInput(BaseModel):
    code: str
    quantity: int = 1


class FinalizeFromItemsRequest(BaseModel):
    items: List[ItemInput]


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    customer_id: int
    cart_id: int
    total: float
    date: datetime
    status: str
    total_weight: float | None = None


class InvoiceDetailOut(InvoiceOut):
    items: List[CartItemOut]
    customer_name: str


class AnalyticsSummary(BaseModel):
    total_revenue: float
    total_paid_invoices: int
    daily_sales: List[dict]
    top_customers: List[dict]

