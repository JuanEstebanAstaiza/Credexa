"""
Endpoints de autenticación
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_admin_user
)
from app.core.config import settings
from app.models.user import Usuario, Rol
from app.schemas.user import (
    Usuario as UsuarioSchema, UsuarioCreate, UsuarioUpdate, LoginRequest, Token,
    PasswordResetRequest, PasswordReset
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/auth/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Iniciar sesión"""
    # Buscar usuario por username o email
    user = db.query(Usuario).filter(
        ((Usuario.username == username) | (Usuario.email == username)) &
        (Usuario.activo == True)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    # Actualizar último login
    user.ultimo_login = func.now()
    db.commit()

    # Crear token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Establecer cookie con el token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UsuarioSchema.from_orm(user)
    }

@router.post("/auth/logout")
async def logout(response: Response):
    """Cerrar sesión"""
    response.delete_cookie(key="access_token")
    return {"message": "Sesión cerrada exitosamente"}

@router.get("/auth/me", response_model=UsuarioSchema)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/perfil", response_model=UsuarioSchema)
async def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    """Obtener perfil completo del usuario actual"""
    return current_user

@router.put("/perfil")
async def actualizar_perfil(
    nombre_completo: str = Form(..., min_length=2, max_length=100),
    username: str = Form(..., min_length=3, max_length=50),
    email: str = Form(..., min_length=5, max_length=100),
    password_actual: str = Form(..., min_length=1),
    password_nueva: Optional[str] = Form(None, min_length=6),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar perfil del usuario actual"""
    from app.core.security import verify_password, get_password_hash

    # Verificar contraseña actual
    if not verify_password(password_actual, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Verificar si el username ya existe (excluyendo el usuario actual)
    if username != current_user.username:
        existing_user = db.query(Usuario).filter(
            Usuario.username == username,
            Usuario.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )

    # Verificar si el email ya existe (excluyendo el usuario actual)
    if email != current_user.email:
        existing_user = db.query(Usuario).filter(
            Usuario.email == email,
            Usuario.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )

    # Actualizar datos básicos
    current_user.nombre_completo = nombre_completo
    current_user.username = username
    current_user.email = email

    # Actualizar contraseña si se proporciona
    if password_nueva:
        current_user.hashed_password = get_password_hash(password_nueva)

    db.commit()
    db.refresh(current_user)

    return {"message": "Perfil actualizado exitosamente", "user": UsuarioSchema.from_orm(current_user)}

@router.post("/auth/register", response_model=UsuarioSchema)
async def register_user(
    user_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Registrar nuevo usuario (solo administradores)"""
    # Verificar si el username ya existe
    existing_user = db.query(Usuario).filter(Usuario.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso",
        )

    # Verificar si el email ya existe
    existing_email = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # Verificar que el rol existe
    rol = db.query(Rol).filter(Rol.id == user_data.rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol no encontrado",
        )

    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    db_user = Usuario(
        nombre_completo=user_data.nombre_completo,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        rol_id=user_data.rol_id
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.put("/auth/users/{user_id}", response_model=UsuarioSchema)
async def update_user(
    user_id: int,
    user_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Actualizar usuario (solo administradores)"""
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Verificar username único si se está cambiando
    if user_data.username and user_data.username != user.username:
        existing_user = db.query(Usuario).filter(Usuario.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso",
            )

    # Verificar email único si se está cambiando
    if user_data.email and user_data.email != user.email:
        existing_email = db.query(Usuario).filter(Usuario.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado",
            )

    # Actualizar campos
    update_data = user_data.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user

@router.delete("/auth/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Eliminar usuario (solo administradores)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario",
        )

    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    db.delete(user)
    db.commit()

    return {"message": "Usuario eliminado exitosamente"}

@router.get("/auth/users", response_model=list[UsuarioSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Obtener lista de usuarios (solo administradores)"""
    users = db.query(Usuario).offset(skip).limit(limit).all()
    return users

@router.post("/auth/password-reset-request")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Solicitar restablecimiento de contraseña"""
    # Por ahora, solo verificamos que el email existe
    # En una implementación completa, enviaríamos un email con token
    user = db.query(Usuario).filter(Usuario.email == reset_data.email).first()

    # Siempre devolver el mismo mensaje por seguridad
    return {
        "message": "Si el email está registrado, recibirás instrucciones para restablecer tu contraseña"
    }

@router.post("/auth/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Restablecer contraseña con token"""
    # En una implementación completa, verificaríamos el token JWT
    # Por ahora, aceptamos cualquier token y reseteamos la contraseña
    # TODO: Implementar tokens de reseteo de contraseña reales

    # Esta es una implementación simplificada para desarrollo
    # En producción, usar tokens temporales con expiración
    try:
        # Decodificar token básico (simplificado)
        user_id = int(reset_data.token)
        user = db.query(Usuario).filter(Usuario.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido",
            )

        # Actualizar contraseña
        user.hashed_password = get_password_hash(reset_data.new_password)
        db.commit()

        return {"message": "Contraseña actualizada exitosamente"}

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido",
        )
