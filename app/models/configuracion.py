"""
Modelo de configuraciones del sistema
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Configuracion(Base):
    __tablename__ = "configuraciones"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)  # Multi-tenant
    clave = Column(String(100), nullable=False, index=True)  # Ya no unique global, solo por empresa
    valor = Column(String(500), nullable=True)
    tipo = Column(String(50), nullable=False, default="string")  # string, int, float, bool
    descripcion = Column(String(255), nullable=True)
    categoria = Column(String(100), nullable=True)

    # Timestamps
    creado_en = Column(DateTime, default=func.now())
    actualizado_en = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    empresa = relationship("Empresa", back_populates="configuraciones")  # Multi-tenant

    def __repr__(self):
        return f"<Configuracion(clave='{self.clave}', valor='{self.valor}')>"
