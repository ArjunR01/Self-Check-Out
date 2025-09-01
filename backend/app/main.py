from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import auth, products, cart, carts, invoices, analytics, customers

app = FastAPI(title="Self-Checkout & Billing API")

# CORS (allow all for dev)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# Routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)  # legacy cart endpoints
app.include_router(carts.router)  # new pluralized carts endpoints
app.include_router(invoices.router)
app.include_router(customers.router)
app.include_router(analytics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


