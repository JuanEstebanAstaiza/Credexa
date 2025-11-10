"""
Esquemas Pydantic para Suscripciones
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import enum


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


class SuscripcionBase(BaseModel):
    """Base schema para Suscripcion"""
    empresa_id: int = Field(..., gt=0)
    plan_id: int = Field(..., gt=0)
    estado: EstadoSuscripcion = EstadoSuscripcion.ACTIVA
    tipo: TipoSuscripcion = TipoSuscripcion.MENSUAL
    precio_pagado: float = Field(..., gt=0)
    metodo_pago: Optional[str] = Field(None, max_length=50)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    renovacion_automatica: bool = True

    # Límites personalizados
    limite_usuarios: Optional[int] = Field(None, gt=0)
    limite_clientes: Optional[int] = Field(None, gt=0)
    limite_prestamos: Optional[int] = Field(None, gt=0)
    limite_almacenamiento_gb: Optional[int] = Field(None, gt=0)

    observaciones: Optional[str] = None


class SuscripcionCreate(SuscripcionBase):
    """Schema para crear nueva suscripción"""
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None

    @validator('fecha_fin')
    def validate_fecha_fin(cls, v, values):
        fecha_inicio = values.get('fecha_inicio')
        if v and fecha_inicio and v <= fecha_inicio:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


class SuscripcionUpdate(BaseModel):
    """Schema para actualizar suscripción"""
    estado: Optional[EstadoSuscripcion] = None
    tipo: Optional[TipoSuscripcion] = None
    precio_pagado: Optional[float] = Field(None, gt=0)
    metodo_pago: Optional[str] = Field(None, max_length=50)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    renovacion_automatica: Optional[bool] = None

    # Límites personalizados
    limite_usuarios: Optional[int] = Field(None, gt=0)
    limite_clientes: Optional[int] = Field(None, gt=0)
    limite_prestamos: Optional[int] = Field(None, gt=0)
    limite_almacenamiento_gb: Optional[int] = Field(None, gt=0)

    observaciones: Optional[str] = None
    fecha_fin: Optional[datetime] = None


class SuscripcionResponse(SuscripcionBase):
    """Schema de respuesta para Suscripcion"""
    id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    fecha_cancelacion: Optional[datetime] = None
    fecha_suspension: Optional[datetime] = None
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    # Información relacionada
    empresa_nombre: Optional[str] = None
    plan_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class SuscripcionDetalleResponse(SuscripcionResponse):
    """Schema detallado de suscripción con información completa"""
    empresa: Optional[dict] = None
    plan: Optional[dict] = None

    # Propiedades calculadas
    esta_activa: Optional[bool] = None
    dias_restantes: Optional[int] = None


class SuscripcionEstadisticas(BaseModel):
    """Estadísticas generales de suscripciones"""
    total_suscripciones: int
    suscripciones_activas: int
    suscripciones_inactivas: int
    suscripciones_suspendidas: int
    suscripciones_canceladas: int
    suscripciones_vencidas: int

    ingresos_mensuales_actuales: float
    ingresos_anuales_estimados: float
    promedio_precio_suscripcion: float

    # Por tipo
    suscripciones_mensuales: int
    suscripciones_anuales: int

    # Nuevas suscripciones este mes
    nuevas_suscripciones_mes: int

