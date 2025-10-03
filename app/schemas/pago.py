"""
Esquemas Pydantic para Pago
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator
from decimal import Decimal

# Esquemas base (sin validaciones restrictivas)
class PagoBase(BaseModel):
    prestamo_id: int
    fecha_pago: datetime
    monto_pagado: Decimal
    tipo_pago: str = "cuota"  # cuota, abono, refinanciacion
    numero_cuota: Optional[int] = None
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    observaciones: Optional[str] = None

    @validator('monto_pagado')
    def validar_monto(cls, v):
        """Validar que el monto pagado sea positivo"""
        if v <= 0:
            raise ValueError('El monto pagado debe ser mayor a cero')
        return v

    @validator('tipo_pago')
    def validar_tipo_pago(cls, v):
        """Validar que el tipo de pago sea válido"""
        tipos_validos = ["cuota", "abono", "refinanciacion"]
        if v not in tipos_validos:
            raise ValueError(f'El tipo de pago debe ser uno de: {", ".join(tipos_validos)}')
        return v

# Esquemas para crear (con validaciones estrictas)
class PagoCreate(PagoBase):
    @validator('fecha_pago')
    def validar_fecha_pago_creacion(cls, v):
        """Validar que la fecha de pago no sea futura (solo para creación)"""
        if v > datetime.now():
            raise ValueError('La fecha de pago no puede ser futura')
        return v

# Esquemas para actualizar
class PagoUpdate(BaseModel):
    prestamo_id: Optional[int] = None
    fecha_pago: Optional[datetime] = None
    monto_pagado: Optional[Decimal] = None
    tipo_pago: Optional[str] = None
    numero_cuota: Optional[int] = None
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    observaciones: Optional[str] = None

# Esquemas para respuesta
class Pago(PagoBase):
    id: int
    capital_pagado: Decimal
    intereses_pagados: Decimal
    creado_en: datetime
    actualizado_en: Optional[datetime]

    class Config:
        from_attributes = True

# Esquemas para filtros y búsqueda
class PagoFiltro(BaseModel):
    prestamo_id: Optional[int] = None
    tipo_pago: Optional[str] = None
    metodo_pago: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    monto_min: Optional[Decimal] = None
    monto_max: Optional[Decimal] = None

class PagoPaginado(BaseModel):
    items: list[Pago]
    total: int
    pagina: int
    por_pagina: int
    paginas_totales: int

# Esquema para registro de pago con cálculo automático
class PagoRegistro(BaseModel):
    prestamo_id: int
    monto_pagado: Decimal
    fecha_pago: Optional[datetime] = None
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    observaciones: Optional[str] = None

    # El cálculo automático se hará en el backend
    tipo_pago: Optional[str] = None  # Se determinará automáticamente

class PagoRegistroConArchivos(BaseModel):
    """Esquema para registrar pago con archivos opcionales de soporte"""
    prestamo_id: int
    monto_pagado: Decimal
    fecha_pago: Optional[datetime] = None
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    observaciones: Optional[str] = None

    # Archivos opcionales de soporte
    archivos_soporte: Optional[List[str]] = None  # Lista de nombres de archivos para FormData
    descripcion_archivos: Optional[str] = None

    # El cálculo automático se hará en el backend
    tipo_pago: Optional[str] = None  # Se determinará automáticamente
