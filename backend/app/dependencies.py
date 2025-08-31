from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_token
from . import models

oauth2_scheme_customer = OAuth2PasswordBearer(tokenUrl="/auth/customer/login")
oauth2_scheme_official = OAuth2PasswordBearer(tokenUrl="/auth/official/login")


def get_current_customer(token: str = Depends(oauth2_scheme_customer), db: Session = Depends(get_db)) -> models.Customer:
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("role") != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a customer token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(models.Customer).filter(models.Customer.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_official(token: str = Depends(oauth2_scheme_official), db: Session = Depends(get_db)) -> models.StoreOfficial:
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("role") not in ("cashier", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an official token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(models.StoreOfficial).filter(models.StoreOfficial.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(official: models.StoreOfficial = Depends(get_current_official)) -> models.StoreOfficial:
    if official.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return official

