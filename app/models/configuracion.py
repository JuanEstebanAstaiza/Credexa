"""
Modelo de configuraciones del sistema
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Configuracion(Base):
    __tablename__ = "configuraciones"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(String(500), nullable=True)
    tipo = Column(String(50), nullable=False, default="string")  # string, int, float, bool
    descripcion = Column(String(255), nullable=True)
    categoria = Column(String(100), nullable=True)

    # Timestamps
    creado_en = Column(DateTime, default=func.now())
    actualizado_en = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Configuracion(clave='{self.clave}', valor='{self.valor}')>"
