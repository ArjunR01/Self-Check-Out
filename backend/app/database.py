import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

# Resolve SQLite relative path to an absolute path rooted at the repo
resolved_db_url = DATABASE_URL
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    # Example: sqlite:///./app.db or sqlite:///app.db -> make absolute path
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    rel_path = DATABASE_URL.replace("sqlite:///", "", 1)
    abs_path = os.path.abspath(os.path.join(repo_root, rel_path))
    # SQLAlchemy absolute path form requires four slashes
    resolved_db_url = f"sqlite:///{abs_path}"

connect_args = {}
if resolved_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(resolved_db_url, echo=False, future=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def init_db():
    from . import models  # ensure models are imported
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

