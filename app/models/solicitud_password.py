"""
Modelo para solicitudes de cambio de contraseña
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SolicitudPassword(Base):
    """Modelo de Solicitudes de Cambio de Contraseña"""
    __tablename__ = "solicitudes_password"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo_solicitud = Column(String(20), nullable=False)  # 'usuario' o 'admin'
    estado = Column(String(20), nullable=False, default="pendiente")  # pendiente, aprobada, rechazada, completada
    nueva_password = Column(String, nullable=True)  # Nueva contraseña (solo para admin)
    motivo = Column(Text, nullable=True)  # Motivo de la solicitud (para usuarios)
    comentarios_admin = Column(Text, nullable=True)  # Comentarios del administrador
    token_verificacion = Column(String(100), unique=True, nullable=True, index=True)  # Token único para validación
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    fecha_respuesta = Column(DateTime(timezone=True), nullable=True)
    respondido_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # Admin que respondió

    # Relaciones
    usuario = relationship("Usuario", back_populates="solicitudes_password", foreign_keys=[usuario_id])
    administrador = relationship("Usuario", foreign_keys=[respondido_por])

    @property
    def esta_pendiente(self) -> bool:
        """Verificar si la solicitud está pendiente"""
        return self.estado == "pendiente"

    @property
    def esta_aprobada(self) -> bool:
        """Verificar si la solicitud está aprobada"""
        return self.estado == "aprobada"

    @property
    def esta_completada(self) -> bool:
        """Verificar si la solicitud está completada"""
        return self.estado == "completada"

    def __repr__(self):
        return f"<SolicitudPassword(id={self.id}, usuario_id={self.usuario_id}, estado='{self.estado}')>"
