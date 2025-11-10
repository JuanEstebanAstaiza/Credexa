"""
Utilidades de seguridad: hash de contraseñas y JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import Usuario
from app.models.empresa import Empresa

# Contexto para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de seguridad para JWT
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Obtener hash de contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token de acceso JWT con información multi-tenant"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Usuario:
    """Obtener usuario actual desde token JWT con información multi-tenant"""
    token = None

    # Intentar obtener token de Authorization header
    if credentials:
        token = credentials.credentials

    # Intentar obtener token de cookie
    if not token and access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("sub")
    tenant_id: int = payload.get("tenant_id")  # Nuevo: obtener tenant_id del token

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener usuario primero
    user = db.query(Usuario).filter(Usuario.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    # Verificar tenant solo si NO es super-admin
    # Los super-admins pueden acceder a todo sin restricciones de tenant
    if not user.is_super_admin and tenant_id:
        if user.empresa_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no pertenece a este tenant",
            )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )

    return user

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    """Obtener usuario actual opcionalmente (para páginas públicas)"""
    try:
        return get_current_user(credentials, access_token, db)
    except HTTPException:
        return None

def get_current_tenant(current_user: Usuario = Depends(get_current_user)) -> Empresa:
    """Obtener el tenant/empresa actual del usuario"""
    # Los super-admins no pertenecen a una empresa específica
    if current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los super-administradores no pertenecen a una empresa específica",
        )

    if not current_user.empresa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no pertenece a ninguna empresa",
        )
    return current_user.empresa


def get_current_tenant_optional(current_user: Usuario = Depends(get_current_user)) -> Optional[Empresa]:
    """Obtener el tenant/empresa actual del usuario (opcional para super-admins)"""
    # Los super-admins no pertenecen a una empresa específica, devolver None
    if current_user.is_super_admin:
        return None

    if not current_user.empresa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no pertenece a ninguna empresa",
        )
    return current_user.empresa

def get_current_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Verificar que el usuario actual sea administrador de su empresa"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador en tu empresa",
        )
    return current_user

def get_current_super_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Verificar que el usuario actual sea super-administrador de toda la plataforma"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de super-administrador",
        )
    return current_user
