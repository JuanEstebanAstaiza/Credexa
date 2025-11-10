"""
Esquemas Pydantic para Planes de Suscripción
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class PlanSuscripcionBase(BaseModel):
    """Base schema para PlanSuscripcion"""
    nombre: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    descripcion: Optional[str] = None
    precio_mensual: float = Field(..., gt=0)
    precio_anual: Optional[float] = Field(None, gt=0)

    # Límites
    max_usuarios: int = Field(1, gt=0)
    max_clientes: int = Field(1, gt=0)
    max_prestamos_activos: int = Field(1, gt=0)
    almacenamiento_gb: int = Field(1, gt=0)

    # Características
    soporte_premium: bool = False
    reportes_avanzados: bool = False
    api_access: bool = False
    integraciones: bool = False
    backup_automatico: bool = True

    # Configuración
    activo: bool = True
    popular: bool = False
    orden: int = 0

    configuracion_extra: Optional[Dict[str, Any]] = None


class PlanSuscripcionCreate(PlanSuscripcionBase):
    """Schema para crear nuevo plan"""
    pass


class PlanSuscripcionUpdate(BaseModel):
    """Schema para actualizar plan"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    descripcion: Optional[str] = None
    precio_mensual: Optional[float] = Field(None, gt=0)
    precio_anual: Optional[float] = Field(None, gt=0)

    # Límites
    max_usuarios: Optional[int] = Field(None, gt=0)
    max_clientes: Optional[int] = Field(None, gt=0)
    max_prestamos_activos: Optional[int] = Field(None, gt=0)
    almacenamiento_gb: Optional[int] = Field(None, gt=0)

    # Características
    soporte_premium: Optional[bool] = None
    reportes_avanzados: Optional[bool] = None
    api_access: Optional[bool] = None
    integraciones: Optional[bool] = None
    backup_automatico: Optional[bool] = None

    # Configuración
    activo: Optional[bool] = None
    popular: Optional[bool] = None
    orden: Optional[int] = None

    configuracion_extra: Optional[Dict[str, Any]] = None


class PlanSuscripcionResponse(PlanSuscripcionBase):
    """Schema de respuesta para PlanSuscripcion"""
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlanSuscripcionStats(BaseModel):
    """Estadísticas de un plan"""
    plan_id: int
    plan_nombre: str
    suscripciones_activas: int
    ingresos_mensuales: float
    ingresos_anuales: float
