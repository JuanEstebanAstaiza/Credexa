"""
Modelo de Planes de Suscripción para el SaaS
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlanSuscripcion(Base):
    """Modelo de Planes de Suscripción SaaS"""
    __tablename__ = "planes_suscripcion"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    precio_mensual = Column(Float, nullable=False)  # En COP
    precio_anual = Column(Float, nullable=True)  # Descuento opcional

    # Límites del plan
    max_usuarios = Column(Integer, nullable=False, default=1)
    max_clientes = Column(Integer, nullable=False, default=100)
    max_prestamos_activos = Column(Integer, nullable=False, default=50)
    almacenamiento_gb = Column(Integer, nullable=False, default=1)

    # Características
    soporte_premium = Column(Boolean, default=False)
    reportes_avanzados = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    integraciones = Column(Boolean, default=False)
    backup_automatico = Column(Boolean, default=True)

    # Configuración del plan
    activo = Column(Boolean, default=True)
    popular = Column(Boolean, default=False)  # Para destacar en la UI
    orden = Column(Integer, default=0)  # Para ordenar en listados

    # Metadata
    configuracion_extra = Column(JSON, nullable=True)  # Configuración adicional en JSON
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    suscripciones = relationship("Suscripcion", back_populates="plan")

    def __repr__(self):
        return f"<PlanSuscripcion(id={self.id}, nombre='{self.nombre}', precio_mensual={self.precio_mensual})>"

