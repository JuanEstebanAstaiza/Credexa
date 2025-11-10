"""
Modelo de Cliente
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Cliente(Base):
    """Modelo de Cliente"""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)  # Multi-tenant
    nombre_completo = Column(String, nullable=False, index=True)
    cedula = Column(String, nullable=False, index=True)  # Ya no unique global, solo por empresa
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    direccion = Column(Text, nullable=True)
    fecha_nacimiento = Column(DateTime, nullable=True)
    ocupacion = Column(String, nullable=True)
    ingresos_mensuales = Column(Integer, nullable=True)  # En pesos colombianos
    referencias_personales = Column(Text, nullable=True)  # JSON o texto con referencias
    activo = Column(Integer, default=1, nullable=False)  # 1=activo, 0=inactivo
    notas = Column(Text, nullable=True)

    # Timestamps
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre_completo}', cedula='{self.cedula}')>"

    @property
    def is_activo(self) -> bool:
        """Verificar si el cliente está activo"""
        return self.activo == 1

    # Relaciones
    empresa = relationship("Empresa", back_populates="clientes")  # Multi-tenant
    prestamos = relationship("Prestamo", back_populates="cliente", cascade="all, delete-orphan")
