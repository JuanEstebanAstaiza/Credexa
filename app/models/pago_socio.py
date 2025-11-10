"""
Modelo de Pago Socio
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PagoSocio(Base):
    """Modelo de Pagos a/de Socios"""
    __tablename__ = "pagos_socio"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)  # Multi-tenant
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False, index=True)

    # Información del pago
    tipo = Column(String, nullable=False)  # 'aporte', 'prestamo', 'devolucion', 'ganancia'
    monto = Column(Numeric(15, 2), nullable=False)
    fecha_pago = Column(DateTime, nullable=False, index=True)
    metodo_pago = Column(String, nullable=True)  # efectivo, transferencia, cheque, etc.
    numero_recibo = Column(String, nullable=True, index=True)  # Ya no unique global, solo por empresa
    descripcion = Column(Text, nullable=True)

    # Información adicional
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=True)  # Si es pago relacionado con préstamo específico
    saldo_anterior = Column(Numeric(15, 2), nullable=False)  # Saldo del socio antes del pago
    saldo_nuevo = Column(Numeric(15, 2), nullable=False)  # Saldo del socio después del pago

    # Usuario que registró el pago
    registrado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Timestamps
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PagoSocio(id={self.id}, socio_id={self.socio_id}, tipo='{self.tipo}', monto={self.monto})>"

    @property
    def es_ingreso_para_socio(self) -> bool:
        """Verificar si este pago representa un ingreso para el socio"""
        return self.tipo in ['devolucion', 'ganancia']

    @property
    def es_egreso_para_socio(self) -> bool:
        """Verificar si este pago representa un egreso para el socio"""
        return self.tipo in ['aporte', 'prestamo']

    # Relaciones
    empresa = relationship("Empresa", back_populates="pagos_socio")  # Multi-tenant
    socio = relationship("Socio", back_populates="pagos_socio")
    prestamo = relationship("Prestamo", back_populates="pagos_socio")
    usuario = relationship("Usuario", back_populates="pagos_socio")
