import os
import sys

# Allow running as a script
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, init_db
from app import models
from app.security import get_password_hash


def run():
    init_db()
    db = SessionLocal()
    try:
        # Create admin official if not exists
        admin_email = "admin@store.example.com"
        admin = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == admin_email).first()
        if not admin:
            admin = models.StoreOfficial(
                name="Admin",
                email=admin_email,
                role="admin",
                hashed_password=get_password_hash("admin123"),
            )
            db.add(admin)

        # Create a cashier account if not exists
        cashier_email = "cashier@store.example.com"
        cashier = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == cashier_email).first()
        if not cashier:
            cashier = models.StoreOfficial(
                name="Cashier",
                email=cashier_email,
                role="cashier",
                hashed_password=get_password_hash("cashier123"),
            )
            db.add(cashier)

        # Seed products with INR prices if none
        if db.query(models.Product).count() == 0:
            products = [
                models.Product(name="Basmati Rice 1kg", description="Premium basmati rice", code="P1001", price_per_unit=120.00, weight_per_unit=1.0, available_qty=200),
                models.Product(name="Toor Dal 1kg", description="Split pigeon peas", code="P1002", price_per_unit=150.00, weight_per_unit=1.0, available_qty=150),
                models.Product(name="Sugar 1kg", description="Refined sugar", code="P1003", price_per_unit=45.00, weight_per_unit=1.0, available_qty=300),
                models.Product(name="Sunflower Oil 1L", description="Refined oil", code="P1004", price_per_unit=160.00, weight_per_unit=0.92, available_qty=120),
                models.Product(name="Milk 1L", description="Toned milk", code="P1005", price_per_unit=60.00, weight_per_unit=1.0, available_qty=180),
                models.Product(name="Bread 400g", description="Whole wheat bread", code="P1006", price_per_unit=40.00, weight_per_unit=0.4, available_qty=100),
            ]
            db.add_all(products)

        # Create two sample customers
        custs = [
            ("Rohit Sharma", "rohit@example.com", "9876543210"),
            ("Ananya Gupta", "ananya@example.com", "9123456780"),
        ]
        for name, email, phone in custs:
            existing = db.query(models.Customer).filter(models.Customer.email == email).first()
            if not existing:
                db.add(models.Customer(name=name, email=email, phone=phone, hashed_password=get_password_hash("password")))

        db.commit()
        print("Seed completed. Admin login: admin@store.example.com / admin123; Cashier: cashier@store.example.com / cashier123")
    finally:
        db.close()


if __name__ == "__main__":
    run()

