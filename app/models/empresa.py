"""
Modelo de Empresa/Tenant para arquitectura multi-tenant SaaS
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Empresa(Base):
    """
    Modelo que representa una empresa prestamista en el sistema SaaS.
    Cada empresa tiene sus propios usuarios, clientes, préstamos, etc.
    """
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)  # Para URLs amigables
    dominio = Column(String(255), nullable=True, unique=True)  # Para subdominios (empresa1.credexa.com)

    # Información de contacto
    email = Column(String(255), nullable=False, unique=True)
    telefono = Column(String(50), nullable=True)
    direccion = Column(Text, nullable=True)

    # Configuración específica de la empresa
    configuracion = Column(JSON, nullable=True, default=dict)  # Configuración personalizada

    # Estado
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    clientes = relationship("Cliente", back_populates="empresa", cascade="all, delete-orphan")
    prestamos = relationship("Prestamo", back_populates="empresa", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="empresa", cascade="all, delete-orphan")
    socios = relationship("Socio", back_populates="empresa", cascade="all, delete-orphan")
    pagos_socio = relationship("PagoSocio", back_populates="empresa", cascade="all, delete-orphan")
    carpetas = relationship("Carpeta", back_populates="empresa", cascade="all, delete-orphan")
    documentos = relationship("Documento", back_populates="empresa", cascade="all, delete-orphan")
    configuraciones = relationship("Configuracion", back_populates="empresa", cascade="all, delete-orphan")
    solicitudes_password = relationship("SolicitudPassword", back_populates="empresa", cascade="all, delete-orphan")
    suscripciones = relationship("Suscripcion", back_populates="empresa", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Empresa(id={self.id}, nombre='{self.nombre}', slug='{self.slug}')>"

    @property
    def url_base(self):
        """Retorna la URL base para esta empresa"""
        if self.dominio:
            return f"https://{self.dominio}"
        return f"/empresa/{self.slug}"

    @property
    def admin_principal(self):
        """Retorna el usuario administrador principal de esta empresa"""
        from .user import Usuario, Rol
        admin_role = Rol.query.filter_by(nombre="admin").first()
        if admin_role:
            return Usuario.query.filter_by(empresa_id=self.id, rol_id=admin_role.id).first()
        return None
