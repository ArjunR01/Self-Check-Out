import os
import sys

# Ensure backend package root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, init_db
from app.routers.auth import official_login
from app.schemas import LoginRequest


def main():
    init_db()
    db = SessionLocal()
    try:
        t = official_login(LoginRequest(email="admin@store.example.com", password="admin123"), db=db)
        print(f"OK role={t.role}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

