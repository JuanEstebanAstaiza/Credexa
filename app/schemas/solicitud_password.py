"""
Esquemas Pydantic para Solicitudes de Cambio de Contraseña
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SolicitudPasswordBase(BaseModel):
    """Base para solicitudes de contraseña"""
    tipo_solicitud: str = Field(..., description="Tipo de solicitud ('usuario' o 'admin')")
    nueva_password: Optional[str] = Field(None, description="Nueva contraseña (solo para admin)")
    motivo: Optional[str] = Field(None, description="Motivo de la solicitud (para usuarios)")
    comentarios_admin: Optional[str] = Field(None, description="Comentarios del administrador")

class SolicitudPasswordCreate(SolicitudPasswordBase):
    """Crear nueva solicitud"""
    pass

class SolicitudPasswordUpdate(BaseModel):
    """Actualizar solicitud"""
    estado: Optional[str] = Field(None, description="Nuevo estado (aprobada, rechazada)")
    nueva_password: Optional[str] = Field(None, description="Nueva contraseña asignada")
    comentarios_admin: Optional[str] = Field(None, description="Comentarios del admin")

class SolicitudPassword(SolicitudPasswordBase):
    """Solicitud completa"""
    id: int
    usuario_id: int
    estado: str
    token_verificacion: Optional[str]
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime]
    respondido_por: Optional[int]

    # Información del usuario solicitante
    usuario_nombre: str
    usuario_username: str
    usuario_rol: str

    # Información del administrador que respondió (si aplica)
    admin_nombre: Optional[str] = None
    admin_username: Optional[str] = None

    class Config:
        from_attributes = True

class SolicitudPasswordPaginado(BaseModel):
    """Respuesta paginada de solicitudes"""
    items: list[SolicitudPassword]
    total: int
    skip: int
    limit: int
