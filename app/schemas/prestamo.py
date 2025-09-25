"""
Esquemas Pydantic para Préstamo
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator
from decimal import Decimal

# Esquemas base
class PrestamoBase(BaseModel):
    cliente_id: int
    socio_id: Optional[int] = None  # Socio que presta el dinero (opcional)
    monto: Decimal
    tasa_interes: float
    plazo_meses: int
    fecha_inicio: datetime
    origen: str = "empresa"  # 'empresa' o 'socio'
    prestamo_padre_id: Optional[int] = None
    es_refinanciacion: Optional[int] = 0
    observaciones: Optional[str] = None

    @validator('monto')
    def validar_monto(cls, v):
        """Validar que el monto sea positivo"""
        if v <= 0:
            raise ValueError('El monto del préstamo debe ser mayor a cero')
        return v

    @validator('tasa_interes')
    def validar_tasa(cls, v):
        """Validar que la tasa de interés sea positiva y razonable"""
        if v < 0:
            raise ValueError('La tasa de interés no puede ser negativa')
        if v > 50:  # Máximo 50% mensual
            raise ValueError('La tasa de interés mensual no puede ser mayor al 50%')
        return v

    @validator('plazo_meses')
    def validar_plazo(cls, v):
        """Validar que el plazo sea positivo y razonable"""
        if v <= 0:
            raise ValueError('El plazo debe ser mayor a cero')
        if v > 360:  # Máximo 30 años
            raise ValueError('El plazo no puede ser mayor a 360 meses (30 años)')
        return v

    @validator('origen')
    def validar_origen(cls, v):
        """Validar que el origen sea válido"""
        if v not in ['empresa', 'socio']:
            raise ValueError('El origen debe ser "empresa" o "socio"')
        return v

    @validator('socio_id', always=True)
    def validar_socio_id(cls, v, values):
        """Validar que socio_id sea requerido cuando origen es 'socio'"""
        origen = values.get('origen', 'empresa')
        if origen == 'socio' and not v:
            raise ValueError('socio_id es requerido cuando el origen es "socio"')
        return v


# Esquemas para crear (con validaciones estrictas)
class PrestamoCreate(PrestamoBase):
    @validator('fecha_inicio')
    def validar_fecha_inicio_creacion(cls, v):
        """Validar que la fecha de inicio no sea anterior a hoy (solo para creación)"""
        if v < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            raise ValueError('La fecha de inicio no puede ser anterior a hoy')
        return v

# Esquemas para actualizar
class PrestamoUpdate(BaseModel):
    cliente_id: Optional[int] = None
    monto: Optional[Decimal] = None
    tasa_interes: Optional[float] = None
    plazo_meses: Optional[int] = None
    fecha_inicio: Optional[datetime] = None
    prestamo_padre_id: Optional[int] = None
    es_refinanciacion: Optional[int] = None
    observaciones: Optional[str] = None

# Esquemas para respuesta
class Prestamo(PrestamoBase):
    id: int
    valor_cuota: Decimal
    numero_cuotas: int
    total_intereses: Decimal
    total_pagar: Decimal
    saldo_pendiente: Decimal
    cuotas_pagadas: int
    estado: str
    creado_en: datetime
    actualizado_en: Optional[datetime]

    # Propiedades calculadas
    cuotas_restantes: Optional[int] = None
    progreso_pago: Optional[float] = None

    # Relación con cliente (opcional para compatibilidad)
    cliente: Optional[dict] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_calculations(cls, prestamo_orm):
        """Crear instancia del esquema con cálculos automáticos"""
        # Preparar datos del cliente si está cargado
        cliente_data = None
        if hasattr(prestamo_orm, 'cliente') and prestamo_orm.cliente:
            cliente_data = {
                'id': prestamo_orm.cliente.id,
                'nombre_completo': prestamo_orm.cliente.nombre_completo,
                'cedula': prestamo_orm.cliente.cedula,
                'telefono': prestamo_orm.cliente.telefono,
                'email': prestamo_orm.cliente.email,
                'activo': prestamo_orm.cliente.activo
            }

        data = {
            'id': prestamo_orm.id,
            'cliente_id': prestamo_orm.cliente_id,
            'monto': prestamo_orm.monto,
            'tasa_interes': prestamo_orm.tasa_interes,
            'plazo_meses': prestamo_orm.plazo_meses,
            'fecha_inicio': prestamo_orm.fecha_inicio,
            'valor_cuota': prestamo_orm.valor_cuota,
            'numero_cuotas': prestamo_orm.numero_cuotas,
            'total_intereses': prestamo_orm.total_intereses,
            'total_pagar': prestamo_orm.total_pagar,
            'saldo_pendiente': prestamo_orm.saldo_pendiente,
            'cuotas_pagadas': prestamo_orm.cuotas_pagadas,
            'estado': prestamo_orm.estado,
            'prestamo_padre_id': prestamo_orm.prestamo_padre_id,
            'es_refinanciacion': prestamo_orm.es_refinanciacion,
            'observaciones': prestamo_orm.observaciones,
            'creado_en': prestamo_orm.creado_en,
            'actualizado_en': prestamo_orm.actualizado_en,
            'cuotas_restantes': prestamo_orm.numero_cuotas - prestamo_orm.cuotas_pagadas,
            'progreso_pago': (prestamo_orm.cuotas_pagadas / prestamo_orm.numero_cuotas * 100) if prestamo_orm.numero_cuotas > 0 else 0,
            'cliente': cliente_data
        }
        return cls(**data)

# Esquemas para refinanciación
class RefinanciacionCreate(BaseModel):
    prestamo_original_id: int
    nuevo_monto: Decimal
    nueva_tasa_interes: float
    nuevo_plazo_meses: int
    observaciones: Optional[str] = None

# Esquemas para filtros y búsqueda
class PrestamoFiltro(BaseModel):
    cliente_id: Optional[int] = None
    estado: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    monto_min: Optional[Decimal] = None
    monto_max: Optional[Decimal] = None

class PrestamoPaginado(BaseModel):
    items: list[Prestamo]
    total: int
    pagina: int
    por_pagina: int
    paginas_totales: int

# Esquemas para estadísticas
class EstadisticasPrestamo(BaseModel):
    total_prestamos: int
    prestamos_activos: int
    prestamos_pagados: int
    prestamos_en_mora: int
    monto_total_prestado: Decimal
    monto_total_pendiente: Decimal
    monto_total_pagado: Decimal
    promedio_tasa_interes: float
