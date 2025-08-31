# Smart Self-Checkout Billing System

A production-ready Smart Self-Checkout system.

- Backend: FastAPI (Python)
- Frontend: React (Vite + Tailwind)
- DB: SQLite for local demo (easy switch to Postgres)
- Auth: Google OAuth for customers; JWT for both customers and officials; officials use email/password
- QR: Invoice code encoded as QR (INV-<uuid>)
- PDF: Invoice PDF with itemized lines, net weights, totals in ₹

All currency displays use Indian Rupees (₹). Default timestamps are stored as UTC and displayed with en-IN locale; IST behavior is documented below.

## Required behavior (implemented)

Public (no login):
- Scan or manually enter product code and add to cart.
- GET /products/{code} validates product; if not found returns 404 with: "Invalid product — not available in this store".
- Anonymous cart is kept client-side; duplicates increase quantity only and show line subtotal and net weight.

Checkout (customer login required):
- Customer logs in with Google OAuth. After OAuth, anonymous cart is persisted server-side.
- POST /carts/attach persists items to a server cart for the customer (deduped, subtotal and net weight computed).
- POST /carts/{cart_id}/checkout creates a pending invoice and returns { invoice_id, qr_code, qr_base64, total, total_net_weight }.
- GET /invoices/{invoice_id}/qr returns the QR PNG; GET /invoices/{invoice_id}/pdf returns a robust PDF.

Store Official (secret login route):
- Official login page is at /official-login (not linked anywhere public).
- Officials sign in with email/password (JWT). Official-only actions:
  - GET /invoices/by-code/{qr_code} to fetch invoice and items
  - POST /invoices/{id}/pay to mark invoice as paid (sets status=paid, paid_at, and official_id)

History & dashboards:
- Customers: GET /customers/me/invoices shows list with status and PDF download.
- Officials: Dashboard summary endpoint GET /analytics/summary with totals and top customers.

Robustness & security:
- All write endpoints protected by JWT and role checks.
- Guards: checkout requires login and non-empty cart; stock validation prevents invoice creation when insufficient; double-pay prevented.
- Consistent JSON errors with friendly messages; frontend shows non-blank loaders/empty states.

## Project structure

- backend/ (FastAPI)
  - app/main.py and routers (auth, products, carts, invoices, customers, analytics)
  - app/models.py (SQLAlchemy models with enums and constraints)
  - app/utils (qr, pdf, mailer)
  - scripts/seed.py (seed data)
  - Dockerfile
- frontend/ (Vite React TypeScript)
  - src/pages/Customer (Scan, Cart, History, Auth)
  - src/pages/Official (Auth, FetchBill, Dashboard)
  - src/lib (axios client, auth)
  - Tailwind configuration
- docker-compose.yml (optional Postgres service)
- .github/workflows/ci.yml (pytest on push)
- docs/ (demo recording helper and placeholder GIF)

## Setup (development)

### Backend

1) Configure env

Create backend/.env from template:

JWT_SECRET=dev_secret_change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=20160
GOOGLE_CLIENT_ID=<your_google_client_id>
DATABASE_URL=sqlite:///./app.db
EMAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=

2) Install and run

python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend

3) Seed data

python backend/scripts/seed.py

Seeds:
- Officials: admin@store.example.com (admin123), cashier@store.example.com (cashier123)
- Customers: rohit@example.com, ananya@example.com (password)
- Products: P1001..P1006 with INR pricing and realistic weights

Switch to Postgres: set DATABASE_URL=postgresql+psycopg2://checkout:checkout@localhost:5432/checkout and use docker-compose up.

### Frontend

1) Configure env

Create frontend/.env.local

VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=<your_google_client_id>

2) Install and run

cd frontend
npm install
npm run dev

Open http://localhost:5173

Secret Official Login (not linked): http://localhost:5173/official-login

## Key API endpoints

- GET /products/{code}
- POST /carts/attach (customer)
- POST /carts/{cart_id}/checkout (customer)
- GET /invoices/{invoice_id}/qr (PNG)
- GET /invoices/{invoice_id}/pdf (PDF)
- GET /invoices/by-code/{qr_code} (official)
- POST /invoices/{id}/pay (official)
- GET /customers/me/invoices (customer)
- Auth: POST /auth/customer/google, POST /auth/official/login

## Tests & CI

Run tests locally:

source backend/.venv/bin/activate
pytest backend/tests -q

A GitHub Actions workflow is included to run pytest on each push.

## Docker & deployment

Local via Docker Compose:

docker compose up --build

Backend on Render:
- Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend
- Set env: JWT_SECRET, DATABASE_URL, GOOGLE_CLIENT_ID

Frontend on Vercel:
- Framework: Vite
- Env: VITE_API_BASE_URL, VITE_GOOGLE_CLIENT_ID

## Currency and timezone

- All amounts use Indian Rupees (₹) formatted to two decimals.
- Frontend uses toLocaleString('en-IN', { currency: 'INR' }).
- Timestamps stored as UTC; displayed with en-IN locale. You can adapt backend to output IST explicitly if required.

## Demo GIF

See docs/record-demo.sh for a quick way to record a 2–3 minute demo (Scan → Cart → Google login → Generate QR → Official scan → Mark paid → History). A placeholder docs/demo.gif is included—replace it with your recording before sharing.

