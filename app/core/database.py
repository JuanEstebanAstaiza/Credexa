"""
Configuración de la base de datos
"""

import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from app.core.config import settings
import pytz

# Zona horaria de Colombia
TIMEZONE_COLOMBIA = pytz.timezone(settings.TIMEZONE)

def convertir_a_colombia(dt):
    """Convierte un datetime UTC a zona horaria de Colombia"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Si no tiene zona horaria, asumir UTC
        dt = pytz.utc.localize(dt)
    return dt.astimezone(TIMEZONE_COLOMBIA)

# Crear engine de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Solo para SQLite
)

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db() -> Session:
    """Dependencia para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Crear todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)
