from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import CustomerCreate, OfficialCreate, OfficialOut, CustomerOut, LoginRequest, Token
from ..security import verify_password, get_password_hash, create_access_token
from fastapi import Header
from ..dependencies import require_admin, get_current_official
from ..security import decode_token
from pydantic import BaseModel, EmailStr

# Google id_token verification
# from google.oauth2 import id_token as google_id_token
# from google.auth.transport import requests as google_requests
from ..config import GOOGLE_CLIENT_ID

router = APIRouter(prefix="/auth", tags=["auth"])


class MeOut(BaseModel):
    role: str
    name: str
    email: EmailStr


@router.post("/customer/signup", response_model=CustomerOut)
def customer_signup(payload: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Customer).filter(models.Customer.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.Customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/customer/login", response_model=Token)
def customer_login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Customer).filter(models.Customer.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.email, role="customer")
    return Token(access_token=token, role="customer")


class GoogleLoginRequest(BaseModel):
    id_token: str


@router.post("/customer/google", response_model=Token)
def customer_google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    try:
        idinfo = google_id_token.verify_oauth2_token(payload.id_token, google_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    email = idinfo.get("email")
    name = idinfo.get("name") or email.split("@")[0]
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google token missing email")

    user = db.query(models.Customer).filter(models.Customer.email == email).first()
    if not user:
        # Create a local record with a random hashed password
        user = models.Customer(
            name=name,
            email=email,
            phone=None,
            hashed_password=get_password_hash(email + "_google"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=user.email, role="customer")
    return Token(access_token=token, role="customer")


@router.post("/official/login", response_model=Token)
def official_login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    role = user.role or "cashier"
    token = create_access_token(subject=user.email, role=role)
    return Token(access_token=token, role=role)


@router.post("/official/signup", response_model=OfficialOut)
def official_signup(payload: OfficialCreate, db: Session = Depends(get_db), _: models.StoreOfficial = Depends(require_admin)):
    existing = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.StoreOfficial(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=MeOut)
def me(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = payload.get("sub")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    if role == "customer":
        user = db.query(models.Customer).filter(models.Customer.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return MeOut(role="customer", name=user.name, email=user.email)
    else:
        user = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return MeOut(role=user.role or "cashier", name=user.name, email=user.email)

