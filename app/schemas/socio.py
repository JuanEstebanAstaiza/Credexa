"""
Schemas Pydantic para Socio
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class SocioBase(BaseModel):
    """Schema base para Socio"""
    nombre_completo: str = Field(..., min_length=1, max_length=255)
    cedula: str = Field(..., min_length=5, max_length=20)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = None
    fecha_nacimiento: Optional[datetime] = None
    ocupacion: Optional[str] = Field(None, max_length=100)
    ingresos_mensuales: Optional[int] = Field(None, ge=0)
    referencias_personales: Optional[str] = None
    activo: int = Field(1, ge=0, le=1)
    notas: Optional[str] = None
    capital_inicial: Decimal = Field(Decimal('0'), ge=0)
    capital_actual: Decimal = Field(Decimal('0'), ge=0)
    porcentaje_participacion: Decimal = Field(Decimal('0'), ge=0, le=100)


class SocioCreate(SocioBase):
    """Schema para crear Socio"""
    pass


class SocioUpdate(BaseModel):
    """Schema para actualizar Socio"""
    nombre_completo: Optional[str] = Field(None, min_length=1, max_length=255)
    cedula: Optional[str] = Field(None, min_length=5, max_length=20)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = None
    fecha_nacimiento: Optional[datetime] = None
    ocupacion: Optional[str] = Field(None, max_length=100)
    ingresos_mensuales: Optional[int] = Field(None, ge=0)
    referencias_personales: Optional[str] = None
    activo: Optional[int] = Field(None, ge=0, le=1)
    notas: Optional[str] = None
    capital_inicial: Optional[Decimal] = Field(None, ge=0)
    capital_actual: Optional[Decimal] = Field(None, ge=0)
    porcentaje_participacion: Optional[Decimal] = Field(None, ge=0, le=100)


class Socio(SocioBase):
    """Schema completo para Socio"""
    id: int
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


class SocioDetalle(Socio):
    """Schema detallado de Socio con estadísticas"""
    capital_disponible: float
    total_invertido: float
    prestamos_activos: int
    prestamos_pagados: int
    pagos_recientes: List[dict] = []

    class Config:
        from_attributes = True


class SocioFiltro(BaseModel):
    """Schema para filtrar socios"""
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    activo: Optional[int] = None
    capital_min: Optional[Decimal] = Field(None, ge=0)
    capital_max: Optional[Decimal] = Field(None, ge=0)
