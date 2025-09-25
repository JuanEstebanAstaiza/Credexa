"""
Schemas Pydantic para PagoSocio
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class PagoSocioBase(BaseModel):
    """Schema base para PagoSocio"""
    socio_id: int
    tipo: str = Field(..., pattern="^(aporte|prestamo|devolucion|ganancia|retiro)$")
    monto: Decimal = Field(..., gt=0)
    fecha_pago: datetime
    metodo_pago: Optional[str] = Field(None, max_length=50)
    numero_recibo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    prestamo_id: Optional[int] = None
    saldo_anterior: Decimal = Field(..., ge=0)
    saldo_nuevo: Decimal = Field(..., ge=0)


class PagoSocioCreate(BaseModel):
    """Schema para crear PagoSocio"""
    socio_id: int
    tipo: str = Field(..., pattern="^(aporte|prestamo|devolucion|ganancia|retiro)$")
    monto: Decimal = Field(..., gt=0)
    fecha_pago: datetime
    metodo_pago: Optional[str] = Field(None, max_length=50)
    numero_recibo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    prestamo_id: Optional[int] = None

    @validator('numero_recibo')
    def validar_numero_recibo_unico(cls, v, values):
        if v:
            # Aquí se podría agregar validación de unicidad del número de recibo
            # Por ahora solo validamos formato básico
            if not v.strip():
                raise ValueError('El número de recibo no puede estar vacío')
        return v


class PagoSocioUpdate(BaseModel):
    """Schema para actualizar PagoSocio"""
    tipo: Optional[str] = Field(None, pattern="^(aporte|prestamo|devolucion|ganancia|retiro)$")
    monto: Optional[Decimal] = Field(None, gt=0)
    fecha_pago: Optional[datetime] = None
    metodo_pago: Optional[str] = Field(None, max_length=50)
    numero_recibo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    prestamo_id: Optional[int] = None


class PagoSocio(PagoSocioBase):
    """Schema completo para PagoSocio"""
    id: int
    registrado_por: Optional[int] = None
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


class PagoSocioDetalle(PagoSocio):
    """Schema detallado de PagoSocio con información relacionada"""
    socio_nombre: str
    prestamo_descripcion: Optional[str] = None
    usuario_registro: Optional[str] = None

    class Config:
        from_attributes = True


class PagoSocioFiltro(BaseModel):
    """Schema para filtrar pagos de socio"""
    socio_id: Optional[int] = None
    tipo: Optional[str] = Field(None, pattern="^(aporte|prestamo|devolucion|ganancia)$")
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    monto_min: Optional[Decimal] = Field(None, ge=0)
    monto_max: Optional[Decimal] = Field(None, ge=0)
    metodo_pago: Optional[str] = None


class PagoSocioEstadistico(BaseModel):
    """Schema para estadísticas de pagos de socio"""
    socio_id: int
    socio_nombre: str
    total_aportes: Decimal
    total_prestamos: Decimal
    total_devoluciones: Decimal
    total_ganancias: Decimal
    saldo_actual: Decimal
    pagos_mes_actual: int
    monto_mes_actual: Decimal
