from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 1) Rezolvăm URL-ul din .env
DATABASE_URL = settings.database_url  # ex: "sqlite:///./data/app.db"

# 2) Dacă e SQLite, ne asigurăm că există folderul "data/"
if DATABASE_URL.startswith("sqlite:///"):
    # scoatem prefixul sqlite:/// și obținem calea relativă
    sqlite_path = DATABASE_URL.replace("sqlite:///", "", 1)
    sqlite_dir = os.path.dirname(sqlite_path)
    if sqlite_dir and not os.path.exists(sqlite_dir):
        os.makedirs(sqlite_dir, exist_ok=True)
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

# 3) Engine & Session (SQLAlchemy 2.x friendly)
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# 4) Dependency FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
