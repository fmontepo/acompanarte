# app/db/session.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# 🔥 cargar variables de entorno
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 🔥 VALIDACIÓN (ACÁ VA)
if not DATABASE_URL:
    raise Exception("DATABASE_URL no está definida")

# 🔥 engine
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()