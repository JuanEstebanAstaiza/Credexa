"""
Modelo de Pago
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Pago(Base):
    """Modelo de Pago"""
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False, index=True)

    # Datos del pago
    fecha_pago = Column(DateTime, nullable=False)
    monto_pagado = Column(Numeric(15, 2), nullable=False)  # Monto total pagado
    tipo_pago = Column(String(20), nullable=False, default="cuota")  # cuota, abono, refinanciacion

    # Desglose del pago
    capital_pagado = Column(Numeric(15, 2), nullable=False, default=0)  # Parte que va al capital
    intereses_pagados = Column(Numeric(15, 2), nullable=False, default=0)  # Parte que va a intereses

    # Información adicional
    numero_cuota = Column(Integer, nullable=True)  # Número de cuota que se está pagando (opcional)
    metodo_pago = Column(String(50), nullable=True)  # efectivo, transferencia, cheque, etc.
    referencia_pago = Column(String(100), nullable=True)  # Número de recibo, comprobante, etc.
    observaciones = Column(Text, nullable=True)  # Notas del pago

    # Timestamps
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    prestamo = relationship("Prestamo", back_populates="pagos")

    def __repr__(self):
        return f"<Pago(id={self.id}, prestamo_id={self.prestamo_id}, monto={self.monto_pagado}, fecha={self.fecha_pago})>"

    @property
    def es_cuota_completa(self) -> bool:
        """Verificar si el pago corresponde a una cuota completa"""
        return self.tipo_pago == "cuota"

    @property
    def es_abono(self) -> bool:
        """Verificar si el pago es un abono"""
        return self.tipo_pago == "abono"
