"""
Endpoints para configuración del sistema y gestión de usuarios
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import Usuario as UsuarioModel, Rol as RolModel
from app.models.configuracion import Configuracion as ConfiguracionModel
from app.schemas.user import Usuario, UsuarioCreate, UsuarioUpdate
from app.schemas.configuracion import (
    Configuracion, ConfiguracionCreate, ConfiguracionUpdate,
    ConfiguracionFiltro
)

# Modelo simple para reset de contraseña
class ResetPasswordRequest(BaseModel):
    nueva_password: str = Field(..., min_length=6, max_length=100)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Endpoints API para Configuraciones

@router.get("/configuraciones", response_model=List[Configuracion])
async def listar_configuraciones(
    categoria: Optional[str] = None,
    tipo: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Listar configuraciones del sistema (solo administradores)"""
    query = db.query(ConfiguracionModel)

    if categoria:
        query = query.filter(ConfiguracionModel.categoria == categoria)
    if tipo:
        query = query.filter(ConfiguracionModel.tipo == tipo)

    configuraciones = query.offset(skip).limit(limit).all()
    return configuraciones


@router.post("/configuraciones", response_model=Configuracion)
async def crear_configuracion(
    configuracion: ConfiguracionCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Crear nueva configuración (solo administradores)"""
    # Verificar si ya existe
    existente = db.query(ConfiguracionModel).filter(
        ConfiguracionModel.clave == configuracion.clave
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una configuración con esta clave"
        )

    # Validar tipo
    if configuracion.tipo not in ["string", "int", "float", "bool"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo debe ser: string, int, float, o bool"
        )

    db_config = ConfiguracionModel(**configuracion.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/configuraciones/{config_id}", response_model=Configuracion)
async def obtener_configuracion(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Obtener configuración por ID (solo administradores)"""
    configuracion = db.query(ConfiguracionModel).filter(ConfiguracionModel.id == config_id).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    return configuracion


@router.put("/configuraciones/{config_id}", response_model=Configuracion)
async def actualizar_configuracion(
    config_id: int,
    configuracion_update: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Actualizar configuración (solo administradores)"""
    configuracion = db.query(Configuracion).filter(ConfiguracionModel.id == config_id).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )

    # Actualizar campos
    update_data = configuracion_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(configuracion, field, value)

    db.commit()
    db.refresh(configuracion)
    return configuracion


@router.delete("/configuraciones/{config_id}")
async def eliminar_configuracion(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Eliminar configuración (solo administradores)"""
    configuracion = db.query(Configuracion).filter(ConfiguracionModel.id == config_id).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )

    db.delete(configuracion)
    db.commit()
    return {"message": "Configuración eliminada exitosamente"}


@router.get("/configuraciones/clave/{clave}")
async def obtener_configuracion_por_clave(
    clave: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener valor de configuración por clave (todos los usuarios autenticados)"""
    configuracion = db.query(ConfiguracionModel).filter(ConfiguracionModel.clave == clave).first()
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )

    # Convertir valor según tipo
    valor = configuracion.valor
    if configuracion.tipo == "int" and valor:
        try:
            valor = int(valor)
        except ValueError:
            valor = 0
    elif configuracion.tipo == "float" and valor:
        try:
            valor = float(valor)
        except ValueError:
            valor = 0.0
    elif configuracion.tipo == "bool" and valor:
        valor = valor.lower() in ("true", "1", "yes", "on")

    return {
        "clave": configuracion.clave,
        "valor": valor,
        "tipo": configuracion.tipo,
        "descripcion": configuracion.descripcion
    }


# Endpoints mejorados para gestión de usuarios

@router.get("/usuarios", response_model=List[Usuario])
async def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    activo: Optional[bool] = None,
    rol_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Listar usuarios con filtros (solo administradores)"""
    query = db.query(UsuarioModel).options(
        # Incluir información del rol
    )

    if activo is not None:
        query = query.filter(UsuarioModel.activo == activo)
    if rol_id is not None:
        query = query.filter(UsuarioModel.rol_id == rol_id)

    usuarios = query.offset(skip).limit(limit).all()
    return usuarios


@router.get("/usuarios/{user_id}", response_model=Usuario)
async def obtener_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Obtener usuario por ID (solo administradores)"""
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


@router.put("/usuarios/{user_id}/estado")
async def cambiar_estado_usuario(
    user_id: int,
    activo: bool,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Activar/desactivar usuario (solo administradores)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio estado"
        )

    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    usuario.activo = activo
    db.commit()

    estado = "activado" if activo else "desactivado"
    return {"message": f"Usuario {estado} exitosamente"}


@router.put("/usuarios/{user_id}/reset-password")
async def reset_password_usuario(
    user_id: int,
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Resetear contraseña de usuario (solo administradores)"""
    from app.core.security import get_password_hash

    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    nueva_password = request.nueva_password

    usuario.hashed_password = get_password_hash(nueva_password)
    db.commit()

    return {"message": "Contraseña reseteada exitosamente"}


# Endpoints para páginas HTML

@router.get("", response_class=HTMLResponse)
async def pagina_configuracion(
    request: Request,
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Página principal de configuración del sistema"""
    return templates.TemplateResponse("configuracion/index.html", {
        "request": request,
        "title": "Configuración del Sistema",
        "user": current_user
    })


@router.get("/usuarios", response_class=HTMLResponse)
async def pagina_gestion_usuarios(
    request: Request,
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Página de gestión de usuarios"""
    return templates.TemplateResponse("configuracion/usuarios.html", {
        "request": request,
        "title": "Gestión de Usuarios",
        "user": current_user
    })


@router.get("/sistema", response_class=HTMLResponse)
async def pagina_config_sistema(
    request: Request,
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Página de configuración del sistema"""
    return templates.TemplateResponse("configuracion/sistema.html", {
        "request": request,
        "title": "Configuración del Sistema",
        "user": current_user
    })
