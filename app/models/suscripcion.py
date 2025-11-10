"""
Modelo de Suscripciones activas para el SaaS
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EstadoSuscripcion(str, enum.Enum):
    """Estados posibles de una suscripción"""
    ACTIVA = "activa"
    INACTIVA = "inactiva"
    SUSPENDIDA = "suspendida"
    CANCELADA = "cancelada"
    VENCIDA = "vencida"


class TipoSuscripcion(str, enum.Enum):
    """Tipos de suscripción"""
    MENSUAL = "mensual"
    ANUAL = "anual"


class Suscripcion(Base):
    """Modelo de Suscripciones SaaS activas"""
    __tablename__ = "suscripciones"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("planes_suscripcion.id"), nullable=False, index=True)

    # Estado y tipo
    estado = Column(Enum(EstadoSuscripcion), default=EstadoSuscripcion.ACTIVA, nullable=False)
    tipo = Column(Enum(TipoSuscripcion), default=TipoSuscripcion.MENSUAL, nullable=False)

    # Fechas importantes
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)  # Para suscripciones con vencimiento
    fecha_cancelacion = Column(DateTime(timezone=True), nullable=True)
    fecha_suspension = Column(DateTime(timezone=True), nullable=True)

    # Información de pago
    precio_pagado = Column(Float, nullable=False)  # Precio actual pagado
    metodo_pago = Column(String(50), nullable=True)  # efectivo, transferencia, etc.
    referencia_pago = Column(String(100), nullable=True)

    # Renovación automática
    renovacion_automatica = Column(Boolean, default=True)

    # Límites actuales (pueden ser diferentes al plan base)
    limite_usuarios = Column(Integer, nullable=True)
    limite_clientes = Column(Integer, nullable=True)
    limite_prestamos = Column(Integer, nullable=True)
    limite_almacenamiento_gb = Column(Integer, nullable=True)

    # Observaciones
    observaciones = Column(Text, nullable=True)

    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    empresa = relationship("Empresa", back_populates="suscripciones")
    plan = relationship("PlanSuscripcion", back_populates="suscripciones")

    @property
    def esta_activa(self):
        """Verifica si la suscripción está activa"""
        from datetime import datetime
        return (
            self.estado == EstadoSuscripcion.ACTIVA and
            (self.fecha_fin is None or self.fecha_fin > datetime.now())
        )

    @property
    def dias_restantes(self):
        """Calcula los días restantes de la suscripción"""
        if self.fecha_fin is None:
            return None
        from datetime import datetime
        delta = self.fecha_fin - datetime.now()
        return max(0, delta.days)

    def __repr__(self):
        return f"<Suscripcion(id={self.id}, empresa_id={self.empresa_id}, plan_id={self.plan_id}, estado={self.estado.value})>"

