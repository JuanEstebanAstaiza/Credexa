"""
Modelo de Socio
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Socio(Base):
    """Modelo de Socio (prestamistas de la empresa)"""
    __tablename__ = "socios"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)  # Multi-tenant
    nombre_completo = Column(String, nullable=False, index=True)
    cedula = Column(String, nullable=False, index=True)  # Ya no unique global, solo por empresa
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    direccion = Column(Text, nullable=True)
    fecha_nacimiento = Column(DateTime, nullable=True)
    ocupacion = Column(String, nullable=True)
    ingresos_mensuales = Column(Integer, nullable=True)  # En pesos colombianos
    referencias_personales = Column(Text, nullable=True)  # JSON o texto con referencias
    activo = Column(Integer, default=1, nullable=False)  # 1=activo, 0=inactivo
    notas = Column(Text, nullable=True)

    # Información financiera específica de socio
    capital_inicial = Column(Numeric(15, 2), default=0, nullable=False)  # Capital inicial aportado
    capital_actual = Column(Numeric(15, 2), default=0, nullable=False)  # Capital actual disponible
    porcentaje_participacion = Column(Numeric(5, 2), default=0, nullable=False)  # % de participación en ganancias

    # Timestamps
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Socio(id={self.id}, nombre='{self.nombre_completo}', cedula='{self.cedula}')>"

    @property
    def is_activo(self) -> bool:
        """Verificar si el socio está activo"""
        return self.activo == 1

    @property
    def capital_disponible(self) -> float:
        """Calcular capital disponible (capital_actual - capital prestado)"""
        capital_prestado = sum(float(pago.monto) for pago in self.pagos_socio if pago.tipo == "prestamo")
        return float(self.capital_actual) - capital_prestado

    @property
    def total_invertido(self) -> float:
        """Calcular total invertido (prestado a la empresa/clientes)"""
        return sum(float(pago.monto) for pago in self.pagos_socio if pago.tipo == "prestamo")

    # Relaciones
    empresa = relationship("Empresa", back_populates="socios")  # Multi-tenant
    prestamos = relationship("Prestamo", back_populates="socio", cascade="all, delete-orphan")
    pagos_socio = relationship("PagoSocio", back_populates="socio", cascade="all, delete-orphan")
