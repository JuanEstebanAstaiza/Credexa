"""
Modelos de Usuario y Rol
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Rol(Base):
    """Modelo de Rol de usuario"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    descripcion = Column(String, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con usuarios
    usuarios = relationship("Usuario", back_populates="rol")

    def __repr__(self):
        return f"<Rol(id={self.id}, nombre='{self.nombre}')>"

class Usuario(Base):
    """Modelo de Usuario"""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    ultimo_login = Column(DateTime(timezone=True), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    pagos_socio = relationship("PagoSocio", back_populates="usuario", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        """Verificar si el usuario es administrador"""
        return self.rol.nombre.lower() == "administrador"

    @property
    def is_digitador(self) -> bool:
        """Verificar si el usuario es digitador"""
        return self.rol.nombre.lower() == "digitador"

    def __repr__(self):
        return f"<Usuario(id={self.id}, username='{self.username}', rol='{self.rol.nombre}')>"
