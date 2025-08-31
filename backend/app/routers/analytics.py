from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..dependencies import get_current_official
from ..schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def summary(db: Session = Depends(get_db), _: models.StoreOfficial = Depends(get_current_official)):
    total_revenue = db.query(func.coalesce(func.sum(models.Invoice.total), 0.0)).filter(models.Invoice.status == models.InvoiceStatus.paid).scalar() or 0.0
    total_paid_invoices = db.query(func.count(models.Invoice.id)).filter(models.Invoice.status == models.InvoiceStatus.paid).scalar() or 0

    # daily sales
    rows = (
        db.query(func.date(models.Invoice.date).label("d"), func.coalesce(func.sum(models.Invoice.total), 0.0))
        .filter(models.Invoice.status == models.InvoiceStatus.paid)
        .group_by(func.date(models.Invoice.date))
        .order_by(func.date(models.Invoice.date))
        .all()
    )
    daily_sales = [{"date": str(r[0]), "total": float(r[1])} for r in rows]

    # top customers by total spent
    rows2 = (
        db.query(models.Customer.id, models.Customer.name, func.coalesce(func.sum(models.Invoice.total), 0.0).label("spent"))
        .join(models.Invoice, models.Invoice.customer_id == models.Customer.id)
        .filter(models.Invoice.status == models.InvoiceStatus.paid)
        .group_by(models.Customer.id, models.Customer.name)
        .order_by(func.sum(models.Invoice.total).desc())
        .limit(5)
        .all()
    )
    top_customers = [{"customer_id": r[0], "name": r[1], "spent": float(r[2])} for r in rows2]

    return AnalyticsSummary(
        total_revenue=float(total_revenue or 0.0),
        total_paid_invoices=int(total_paid_invoices or 0),
        daily_sales=daily_sales,
        top_customers=top_customers,
    )

