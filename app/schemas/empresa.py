"""
Esquemas Pydantic para el modelo Empresa (tenant)
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class EmpresaBase(BaseModel):
    """Base schema para Empresa"""
    nombre: str
    slug: str
    dominio: Optional[str] = None
    email: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    configuracion: Optional[Dict[str, Any]] = None
    activo: bool = True

    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('El slug solo puede contener letras minúsculas, números y guiones')
        if len(v) < 3:
            raise ValueError('El slug debe tener al menos 3 caracteres')
        return v

    @validator('telefono')
    def validate_telefono(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v


class AdminCreate(BaseModel):
    """Schema para datos del administrador al crear empresa"""
    nombre_completo: str
    username: str
    email: str
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

class EmpresaCreate(EmpresaBase):
    """Schema para crear nueva empresa"""
    admin_data: AdminCreate  # Datos del administrador de la nueva empresa


class EmpresaUpdate(BaseModel):
    """Schema para actualizar empresa"""
    nombre: Optional[str] = None
    slug: Optional[str] = None
    dominio: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    configuracion: Optional[Dict[str, Any]] = None
    activo: Optional[bool] = None

    @validator('slug')
    def validate_slug(cls, v):
        if v and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('El slug solo puede contener letras minúsculas, números y guiones')
        return v

    @validator('telefono')
    def validate_telefono(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v


class EmpresaResponse(EmpresaBase):
    """Schema de respuesta para Empresa"""
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmpresaStats(BaseModel):
    """Schema para estadísticas de empresa"""
    empresa: str
    usuarios_activos: int
    total_clientes: int
    total_prestamos: int
    prestamos_activos: int
    total_cartera: float
    activo: bool
