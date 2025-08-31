Self-Checkout & Billing API (FastAPI)

Setup
1) Create env file
   cp .env.example .env
   # edit values as needed (keep SQLite for local)

2) Create venv and install deps
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

3) Run dev server
   uvicorn app.main:app --reload

4) Seed data (optional but recommended)
   python backend/scripts/seed.py   # if running from project root
   # or
   python scripts/seed.py           # if running from backend directory

Auth Endpoints
- POST /auth/customer/signup
- POST /auth/customer/login
- POST /auth/official/login
- POST /auth/official/signup (admin token required)

Core Endpoints
- Products: GET /products/, GET /products/{id}, POST /products/ (official)
- Cart: GET /cart/, POST /cart/scan, POST /cart/update, POST /cart/finalize
- Invoices: GET /invoices/by-code/{code} (official), POST /invoices/{code}/mark_paid (official)
            GET /invoices/{code}/pdf (customer owner), GET /invoices/{code}/qr (png), GET /invoices/me/history
- Analytics: GET /analytics/summary (official)

Notes
- QR code contains the invoice code; the frontend can render it directly.
- PDF generation uses reportlab; email sending requires EMAIL_ENABLED=true and SMTP configured.
- Switch to Postgres by setting DATABASE_URL.

