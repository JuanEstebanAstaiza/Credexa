"""
Endpoints de autenticación
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, Query
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_admin_user, get_current_user_optional, security
)
from jose import JWTError, jwt
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

# ====================
# RECUPERACIÓN DE CONTRASEÑA
# ====================
import secrets

@router.post("/auth/solicitar-cambio-password")
async def solicitar_cambio_password(
    motivo: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solicitar cambio de contraseña (para digitadores)"""
    from app.models.solicitud_password import SolicitudPassword

    # Solo usuarios no administradores pueden solicitar cambio
    if current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los administradores deben cambiar su contraseña directamente",
        )

    # Verificar si ya tiene una solicitud pendiente
    solicitud_pendiente = db.query(SolicitudPassword).filter(
        SolicitudPassword.usuario_id == current_user.id,
        SolicitudPassword.estado == "pendiente"
    ).first()

    if solicitud_pendiente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes una solicitud de cambio de contraseña pendiente",
        )

    # Crear nueva solicitud
    nueva_solicitud = SolicitudPassword(
        usuario_id=current_user.id,
        tipo_solicitud="usuario",
        motivo=motivo,
        token_verificacion=secrets.token_urlsafe(32)
    )

    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)

    return {"message": "Solicitud de cambio de contraseña enviada al administrador"}

@router.get("/auth/solicitudes-password", response_model=dict)
async def listar_solicitudes_password(
    skip: int = 0,
    limit: int = 10,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Listar solicitudes de cambio de contraseña (solo admin)"""
    from app.models.solicitud_password import SolicitudPassword

    query = db.query(
        SolicitudPassword,
        Usuario.nombre_completo.label('usuario_nombre'),
        Usuario.username.label('usuario_username'),
        Usuario.rol.label('usuario_rol')
    ).join(
        Usuario, SolicitudPassword.usuario_id == Usuario.id
    )

    if estado:
        query = query.filter(SolicitudPassword.estado == estado)

    # Obtener total
    total = query.count()

    # Aplicar paginación y ordenar
    solicitudes = query.order_by(
        SolicitudPassword.fecha_solicitud.desc()
    ).offset(skip).limit(limit).all()

    # Formatear respuesta
    items = []
    for sol, nombre, username, rol in solicitudes:
        item = {
            "id": sol.id,
            "usuario_id": sol.usuario_id,
            "tipo_solicitud": sol.tipo_solicitud,
            "estado": sol.estado,
            "nueva_password": sol.nueva_password,
            "motivo": sol.motivo,
            "comentarios_admin": sol.comentarios_admin,
            "token_verificacion": sol.token_verificacion,
            "fecha_solicitud": sol.fecha_solicitud,
            "fecha_respuesta": sol.fecha_respuesta,
            "respondido_por": sol.respondido_por,
            "usuario_nombre": nombre,
            "usuario_username": username,
            "usuario_rol": rol.nombre if rol else "Sin rol"
        }

        # Agregar info del admin si aplica
        if sol.respondido_por:
            admin = db.query(Usuario).filter(Usuario.id == sol.respondido_por).first()
            if admin:
                item["admin_nombre"] = admin.nombre_completo
                item["admin_username"] = admin.username

        items.append(item)

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.put("/auth/solicitudes-password/{solicitud_id}")
async def responder_solicitud_password(
    solicitud_id: int,
    respuesta: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Responder a una solicitud de cambio de contraseña (solo admin)"""
    from app.models.solicitud_password import SolicitudPassword

    solicitud = db.query(SolicitudPassword).filter(SolicitudPassword.id == solicitud_id).first()

    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada",
        )

    if solicitud.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta solicitud ya ha sido procesada",
        )

    # Actualizar solicitud
    solicitud.estado = respuesta.estado or solicitud.estado
    solicitud.comentarios_admin = respuesta.comentarios_admin or solicitud.comentarios_admin
    solicitud.fecha_respuesta = func.now()
    solicitud.respondido_por = current_user.id

    # Si se aprueba, actualizar la contraseña del usuario
    if solicitud.estado == "aprobada":
        usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()

        if respuesta.nueva_password:
            # Usar la contraseña proporcionada por el admin
            usuario.hashed_password = get_password_hash(respuesta.nueva_password)
            solicitud.nueva_password = respuesta.nueva_password  # Guardar para referencia
        else:
            # Generar una contraseña aleatoria
            nueva_password = secrets.token_urlsafe(8)
            usuario.hashed_password = get_password_hash(nueva_password)
            solicitud.nueva_password = nueva_password

        solicitud.estado = "completada"  # Marcar como completada inmediatamente

    db.commit()

    return {"message": f"Solicitud {'aprobada' if solicitud.estado == 'completada' else 'rechazada'} exitosamente"}

@router.post("/auth/cambiar-password-admin")
async def cambiar_password_admin(
    usuario_id: int = Form(...),
    nueva_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Cambiar contraseña de un usuario directamente (solo admin)"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Actualizar contraseña
    usuario.hashed_password = get_password_hash(nueva_password)
    db.commit()

    return {"message": f"Contraseña de {usuario.nombre_completo} actualizada exitosamente"}

@router.post("/auth/cambiar-mi-password-admin")
async def cambiar_mi_password_admin(
    nueva_password: str = Form(...),
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cambiar contraseña del admin usando token temporal de verificación"""
    try:
        # Decodificar y verificar el token temporal
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        verified: bool = payload.get("verified", False)

        if not user_id or not verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de verificación inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Obtener el usuario
        usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que sea administrador
        if not usuario.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción"
            )

        # Cambiar la contraseña
        usuario.hashed_password = get_password_hash(nueva_password)
        db.commit()

        return {"message": f"Contraseña actualizada exitosamente. Ahora puedes iniciar sesión normalmente."}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de verificación inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/auth/verificar-admin")
async def verificar_admin(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Verificar que un usuario es administrador sin requerir contraseña"""
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    if not username or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario y email son requeridos",
        )

    # Buscar usuario que coincida con username y email
    usuario = db.query(Usuario).join(Rol).filter(
        Usuario.username == username,
        Usuario.email == email,
        Usuario.activo == True,
        Rol.nombre == "admin"  # Solo admins
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administrador inválidas",
        )

    # Generar un token temporal para este admin verificado
    import secrets
    from datetime import datetime, timedelta
    from app.core.security import create_access_token

    # Crear token con expiración corta (15 minutos)
    token_data = {
        "sub": str(usuario.id),
        "username": usuario.username,
        "role": "admin",
        "verified": True,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }

    access_token = create_access_token(token_data)

    return {
        "message": "Verificación exitosa",
        "usuario": {
            "id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "username": usuario.username
        },
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 900  # 15 minutos en segundos
    }

@router.get("/auth/usuarios")
async def listar_usuarios(
    skip: int = 0,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Listar usuarios para selección (solo admin)"""
    # Obtener usuarios con paginación
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()

    # Formatear respuesta
    result = []
    for usuario in usuarios:
        result.append({
            "id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "username": usuario.username,
            "email": usuario.email,
            "rol_id": usuario.rol_id,
            "activo": usuario.activo
        })

    return {
        "items": result,
        "total": len(result),
        "skip": skip,
        "limit": limit
    }
