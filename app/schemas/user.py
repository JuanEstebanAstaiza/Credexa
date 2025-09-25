"""
Esquemas Pydantic para Usuario y Rol
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Esquemas base
class RolBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class UsuarioBase(BaseModel):
    nombre_completo: str
    username: str
    email: EmailStr
    rol_id: int

# Esquemas para crear
class RolCreate(RolBase):
    pass

class UsuarioCreate(UsuarioBase):
    password: str

# Esquemas para actualizar
class RolUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    rol_id: Optional[int] = None
    activo: Optional[bool] = None
    password: Optional[str] = None

# Esquemas para respuesta
class Rol(RolBase):
    id: int
    activo: bool
    creado_en: datetime
    actualizado_en: Optional[datetime]

    class Config:
        from_attributes = True

class Usuario(UsuarioBase):
    id: int
    activo: bool
    ultimo_login: Optional[datetime]
    creado_en: datetime
    actualizado_en: Optional[datetime]
    rol: Rol
    is_admin: bool
    is_digitador: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Crear instancia desde objeto ORM incluyendo propiedades calculadas"""
        data = super().from_orm(obj).__dict__
        data['is_admin'] = obj.is_admin
        data['is_digitador'] = obj.is_digitador
        return cls(**data)

# Esquemas para autenticación
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Usuario

class TokenData(BaseModel):
    username: Optional[str] = None

# Esquemas para recuperación de contraseña
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
