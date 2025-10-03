"""
Esquemas para reportes del sistema
"""

from datetime import datetime, date
from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class ReportePagoFiltro(BaseModel):
    """Filtros para reportes de pagos"""
    fecha_desde: Union[datetime, date, str]
    fecha_hasta: Union[datetime, date, str]
    tipo_pago: Optional[str] = None
    metodo_pago: Optional[str] = None
    prestamo_id: Optional[int] = None
    cliente_id: Optional[int] = None
    cliente_nombre: Optional[str] = None
    cliente_cedula: Optional[str] = None
    monto_min: Optional[Decimal] = None
    monto_max: Optional[Decimal] = None

    @field_validator('fecha_desde', 'fecha_hasta', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        if isinstance(v, str):
            # Si es string, intentar parsear como date primero, luego como datetime
            try:
                # Intentar parsear como YYYY-MM-DD
                if len(v) == 10 and v.count('-') == 2:
                    parsed_date = date.fromisoformat(v)
                    return datetime.combine(parsed_date, datetime.min.time())
                else:
                    return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Formato de fecha inválido: {v}")
        elif isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        return v


class ReporteMorosoFiltro(BaseModel):
    """Filtros para reportes de clientes morosos"""
    dias_mora_min: Optional[int] = Field(default=1, ge=1)
    monto_min: Optional[Decimal] = Field(default=None, ge=0)
    cliente_id: Optional[int] = None
    cliente_nombre: Optional[str] = None
    cliente_cedula: Optional[str] = None


class ReportePago(BaseModel):
    """Modelo para reporte de pago individual"""
    id: int
    fecha_pago: datetime
    monto_pagado: Decimal
    tipo_pago: str
    metodo_pago: Optional[str]
    numero_cuota: Optional[int]
    capital_pagado: Decimal
    intereses_pagados: Decimal
    referencia_pago: Optional[str]

    # Información del préstamo
    prestamo_id: int
    prestamo_monto: Decimal
    prestamo_estado: str

    # Información del cliente
    cliente_id: int
    cliente_nombre: str
    cliente_cedula: str

    class Config:
        from_attributes = True


class ReporteMoroso(BaseModel):
    """Modelo para reporte de cliente moroso"""
    cliente_id: int
    cliente_nombre: str
    cliente_cedula: str
    cliente_telefono: Optional[str]
    prestamo_id: int
    prestamo_monto: Decimal
    prestamo_fecha_inicio: datetime
    saldo_pendiente: Decimal
    cuotas_pagadas: int
    cuotas_totales: int
    dias_mora: int
    monto_mora: Decimal
    ultima_cuota_fecha: Optional[datetime]

    class Config:
        from_attributes = True


class ReporteEstadistico(BaseModel):
    """Modelo para estadísticas generales del reporte"""
    total_pagos: int
    monto_total_pagos: Decimal
    pagos_dia_actual: int
    monto_dia_actual: Decimal
    pagos_mes_actual: int
    monto_mes_actual: Decimal
    clientes_morosos: int
    monto_mora_total: Decimal
    prestamos_activos: int
    prestamos_pagados: int
