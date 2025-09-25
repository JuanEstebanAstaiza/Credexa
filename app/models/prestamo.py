"""
Modelo de Préstamo
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Prestamo(Base):
    """Modelo de Préstamo"""
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=True, index=True)  # Socio que presta el dinero

    # Datos del préstamo
    monto = Column(Numeric(15, 2), nullable=False)  # Monto total del préstamo
    tasa_interes = Column(Float, nullable=False)  # Tasa de interés mensual (%)
    plazo_meses = Column(Integer, nullable=False)  # Plazo en meses
    fecha_inicio = Column(DateTime, nullable=False)  # Fecha de inicio del préstamo

    # Cálculos automáticos
    valor_cuota = Column(Numeric(15, 2), nullable=False)  # Valor de cada cuota
    numero_cuotas = Column(Integer, nullable=False)  # Número total de cuotas
    total_intereses = Column(Numeric(15, 2), nullable=False)  # Total de intereses a pagar
    total_pagar = Column(Numeric(15, 2), nullable=False)  # Monto total a pagar (capital + intereses)

    # Estado y seguimiento
    saldo_pendiente = Column(Numeric(15, 2), nullable=False, default=0)  # Saldo pendiente por pagar
    cuotas_pagadas = Column(Integer, nullable=False, default=0)  # Número de cuotas pagadas
    estado = Column(String(20), nullable=False, default="activo")  # activo, pagado, mora, refinanciado, cancelado

    # Refinanciación (opcional)
    prestamo_padre_id = Column(Integer, ForeignKey("prestamos.id"), nullable=True)  # Para refinanciaciones
    es_refinanciacion = Column(Integer, default=0, nullable=False)  # 1 si es refinanciación, 0 si no

    # Información adicional
    origen = Column(String(20), nullable=False, default="empresa")  # 'empresa' o 'socio'
    observaciones = Column(Text, nullable=True)  # Notas del préstamo

    # Timestamps
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    cliente = relationship("Cliente", back_populates="prestamos")
    socio = relationship("Socio", back_populates="prestamos")
    pagos = relationship("Pago", back_populates="prestamo", cascade="all, delete-orphan")
    pagos_socio = relationship("PagoSocio", back_populates="prestamo", cascade="all, delete-orphan")

    # Relación para refinanciaciones
    refinanciaciones = relationship("Prestamo", backref="prestamo_padre", remote_side=[id])

    def __repr__(self):
        return f"<Prestamo(id={self.id}, cliente_id={self.cliente_id}, monto={self.monto}, estado='{self.estado}')>"

    @property
    def esta_activo(self) -> bool:
        """Verificar si el préstamo está activo"""
        return self.estado == "activo"

    @property
    def esta_pagado(self) -> bool:
        """Verificar si el préstamo está completamente pagado"""
        return self.estado == "pagado"

    @property
    def esta_en_mora(self) -> bool:
        """Verificar si el préstamo está en mora"""
        return self.estado == "mora"

    @property
    def cuotas_restantes(self) -> int:
        """Calcular cuotas restantes por pagar"""
        return self.numero_cuotas - self.cuotas_pagadas

    @property
    def progreso_pago(self) -> float:
        """Calcular porcentaje de progreso de pago"""
        if self.numero_cuotas == 0:
            return 100.0
        return (self.cuotas_pagadas / self.numero_cuotas) * 100.0

    def calcular_cuota(self) -> float:
        """
        Calcular el valor de la cuota usando fórmula de amortización
        Cuota = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
        Donde:
        - P = monto del préstamo
        - r = tasa de interés mensual (decimal)
        - n = número de cuotas
        """
        if self.plazo_meses == 0:
            return float(self.monto)

        r = self.tasa_interes / 100  # Convertir porcentaje a decimal
        n = self.plazo_meses

        if r == 0:
            # Si no hay interés, dividir el monto por el número de cuotas
            return float(self.monto) / n

        # Fórmula de amortización
        cuota = float(self.monto) * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(cuota, 2)

    def actualizar_estado(self):
        """Actualizar el estado del préstamo basado en los pagos"""
        if self.saldo_pendiente <= 0:
            self.estado = "pagado"
        elif self.cuotas_pagadas > 0:  # Lógica simplificada para mora
            # Aquí se podría implementar lógica más compleja para determinar mora
            # Por ahora, mantenemos el estado actual
            pass
