import os
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient

# Set test database before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test_app.db"

from app.main import app  # noqa: E402
from app.database import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Ensure fresh DB for tests
    try:
        if os.path.exists("test_app.db"):
            os.remove("test_app.db")
    except Exception:
        pass
    init_db()
    yield
    try:
        if os.path.exists("test_app.db"):
            os.remove("test_app.db")
    except Exception:
        pass


def client():
    return TestClient(app)


def signup_and_login_customer(c: TestClient, email="testuser@example.com", password="password"):
    c.post("/auth/customer/signup", json={
        "name": "Test User",
        "email": email,
        "phone": "9999999999",
        "password": password
    })
    r = c.post("/auth/customer/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return token


def login_official(c: TestClient):
    # Ensure there is a cashier official; create directly via DB if missing
    from app.database import SessionLocal
    from app import models
    from app.security import get_password_hash
    db = SessionLocal()
    try:
        cashier = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == "cashier@test.local").first()
        if not cashier:
            cashier = models.StoreOfficial(
                name="Test Cashier",
                email="cashier@test.local",
                role="cashier",
                hashed_password=get_password_hash("cashier123"),
            )
            db.add(cashier)
            db.commit()
    finally:
        db.close()
    r = c.post("/auth/official/login", json={"email": "cashier@test.local", "password": "cashier123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def ensure_products(c: TestClient):
    # Try fetching P1001; if not exists, seed minimal products directly via ORM
    r = c.get("/products/P1001")
    if r.status_code == 200:
        return
    from app.database import SessionLocal
    from app import models
    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            products = [
                models.Product(name="Basmati Rice 1kg", description="Premium basmati rice", code="P1001", price_per_unit=120.00, weight_per_unit=1.0, available_qty=200),
                models.Product(name="Toor Dal 1kg", description="Split pigeon peas", code="P1002", price_per_unit=150.00, weight_per_unit=1.0, available_qty=150),
                models.Product(name="Milk 1L", description="Toned milk", code="P1005", price_per_unit=60.00, weight_per_unit=1.0, available_qty=180),
            ]
            db.add_all(products)
            db.commit()
    finally:
        db.close()


def test_product_lookup_by_code():
    c = TestClient(app)
    ensure_products(c)
    r = c.get("/products/P1001")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == "P1001"


def test_checkout_creates_invoice_and_items():
    c = TestClient(app)
    ensure_products(c)
    token = signup_and_login_customer(c)

    # Attach cart
    r = c.post("/carts/attach", headers={"Authorization": f"Bearer {token}"}, json={
        "items": [{"code": "P1001", "quantity": 2}]
    })
    assert r.status_code == 200
    cart_id = r.json()["cart_id"]

    # Checkout
    r = c.post(f"/carts/{cart_id}/checkout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "invoice_id" in data
    assert data["qr_code"].startswith("INV-")


def test_insufficient_stock():
    c = TestClient(app)
    ensure_products(c)
    token = signup_and_login_customer(c, email="stock@test.com")

    # Attach too many
    r = c.post("/carts/attach", headers={"Authorization": f"Bearer {token}"}, json={
        "items": [{"code": "P1001", "quantity": 999999}]
    })
    assert r.status_code == 200
    cart_id = r.json()["cart_id"]

    r = c.post(f"/carts/{cart_id}/checkout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "Insufficient stock" in r.json()["detail"]


def test_official_pay_and_double_pay_prevented():
    c = TestClient(app)
    ensure_products(c)

    # Setup: customer creates pending invoice
    token = signup_and_login_customer(c, email="pay@test.com")
    r = c.post("/carts/attach", headers={"Authorization": f"Bearer {token}"}, json={
        "items": [{"code": "P1002", "quantity": 1}]
    })
    cart_id = r.json()["cart_id"]
    r = c.post(f"/carts/{cart_id}/checkout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    inv_id = r.json()["invoice_id"]

    # Pay requires official token
    r = c.post(f"/invoices/{inv_id}/pay")
    assert r.status_code in (401, 403)

    official_token = login_official(c)
    r = c.post(f"/invoices/{inv_id}/pay", headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 200

    # Double pay prevented
    r = c.post(f"/invoices/{inv_id}/pay", headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 400
    assert r.json()["detail"].lower().find("already") != -1


def test_invalid_product_message():
    c = TestClient(app)
    r = c.get("/products/NON_EXISTENT_CODE")
    assert r.status_code == 404
    assert r.json()["detail"] == "Invalid product — not available in this store"


def test_attach_requires_login():
    c = TestClient(app)
    r = c.post("/carts/attach", json={"items": [{"code": "P1001", "quantity": 1}]})
    assert r.status_code in (401, 403)

