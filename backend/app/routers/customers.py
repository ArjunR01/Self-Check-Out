from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_customer
from .. import models
from ..schemas import InvoiceOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/me/invoices", response_model=list[InvoiceOut])
def my_invoices(db: Session = Depends(get_db), customer: models.Customer = Depends(get_current_customer)):
    invoices = (
        db.query(models.Invoice)
        .filter(models.Invoice.customer_id == customer.id)
        .order_by(models.Invoice.date.desc())
        .all()
    )
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

