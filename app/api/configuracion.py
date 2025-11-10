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
from app.core.security import get_current_user, get_current_admin_user, get_current_tenant
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
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

# Modelo para configuración de email
class EmailConfig(BaseModel):
    smtp_server: str = Field(..., min_length=1)
    smtp_port: int = Field(..., ge=1, le=65535)
    smtp_username: str = Field(..., min_length=1)
    smtp_password: str = Field(..., min_length=1)
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    email_from: str = Field(..., min_length=1)
    email_from_name: str = Field(..., min_length=1)

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
    current_user: UsuarioModel = Depends(get_current_admin_user),
    tenant = Depends(get_current_tenant)
):
    """Listar configuraciones del sistema (solo administradores)"""
    query = db.query(ConfiguracionModel).filter(ConfiguracionModel.empresa_id == tenant.id)

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
    current_user: UsuarioModel = Depends(get_current_admin_user),
    tenant = Depends(get_current_tenant)
):
    """Crear nueva configuración (solo administradores)"""
    # Verificar si ya existe en esta empresa
    existente = db.query(ConfiguracionModel).filter(
        ConfiguracionModel.clave == configuracion.clave,
        ConfiguracionModel.empresa_id == tenant.id
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una configuración con esta clave en su empresa"
        )

    # Validar tipo
    if configuracion.tipo not in ["string", "int", "float", "bool"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo debe ser: string, int, float, o bool"
        )

    # Crear configuración con empresa_id
    config_dict = configuracion.model_dump()
    config_dict["empresa_id"] = tenant.id
    db_config = ConfiguracionModel(**config_dict)
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

# Endpoints para configuración de email

@router.get("/email/config")
async def obtener_config_email(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Obtener configuración actual de email"""
    from app.services.email_service import email_service

    # Leer configuración desde la base de datos
    email_configs_db = {}
    configuraciones = db.query(ConfiguracionModel).filter(
        ConfiguracionModel.categoria == "email"
    ).all()

    for config in configuraciones:
        if config.clave == "smtp_port":
            email_configs_db[config.clave] = int(config.valor) if config.valor.isdigit() else 587
        elif config.clave in ["smtp_use_tls", "smtp_use_ssl"]:
            email_configs_db[config.clave] = config.valor.lower() == "true"
        else:
            email_configs_db[config.clave] = config.valor or ""

    # Usar valores de BD si existen, sino los valores por defecto del servicio
    config_data = {
        "smtp_server": email_configs_db.get("smtp_server", email_service.smtp_server),
        "smtp_port": email_configs_db.get("smtp_port", email_service.smtp_port),
        "smtp_username": email_configs_db.get("smtp_username", email_service.smtp_username),
        "smtp_use_tls": email_configs_db.get("smtp_use_tls", email_service.use_tls),
        "smtp_use_ssl": email_configs_db.get("smtp_use_ssl", email_service.use_ssl),
        "email_from": email_configs_db.get("email_from", email_service.email_from),
        "email_from_name": email_configs_db.get("email_from_name", email_service.email_from_name),
    }

    # Verificar si está configurado (al menos servidor, usuario y contraseña)
    is_configured = bool(
        config_data["smtp_server"] and
        config_data["smtp_username"] and
        config_data["email_from"]
    )

    config_data["is_configured"] = is_configured
    return config_data

@router.post("/email/config")
async def configurar_email(
    config: EmailConfig,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Configurar el servicio de email SMTP"""
    try:
        # Guardar configuración en la base de datos
        email_configs = {
            "smtp_server": config.smtp_server,
            "smtp_port": str(config.smtp_port),
            "smtp_username": config.smtp_username,
            "smtp_password": config.smtp_password,
            "smtp_use_tls": "true" if config.smtp_use_tls else "false",
            "smtp_use_ssl": "true" if config.smtp_use_ssl else "false",
            "email_from": config.email_from,
            "email_from_name": config.email_from_name
        }

        for clave, valor in email_configs.items():
            # Buscar configuración existente o crear nueva
            configuracion = db.query(ConfiguracionModel).filter(
                ConfiguracionModel.clave == clave,
                ConfiguracionModel.categoria == "email"
            ).first()

            if configuracion:
                configuracion.valor = valor
            else:
                nueva_config = ConfiguracionModel(
                    clave=clave,
                    valor=valor,
                    tipo="string",
                    descripcion=f"Configuración SMTP: {clave}",
                    categoria="email"
                )
                db.add(nueva_config)

        db.commit()

        # Actualizar la configuración global (esto requiere reinicio del servidor)
        # Nota: En producción, se podría implementar un sistema de cache o recarga de config

        # Intentar validar la configuración enviando un email de prueba
        from app.services.email_service import EmailService

        # Crear instancia temporal con la nueva configuración
        test_service = EmailService()
        test_service.smtp_server = config.smtp_server
        test_service.smtp_port = config.smtp_port
        test_service.smtp_username = config.smtp_username
        test_service.smtp_password = config.smtp_password
        test_service.use_tls = config.smtp_use_tls
        test_service.use_ssl = config.smtp_use_ssl
        test_service.email_from = config.email_from
        test_service.email_from_name = config.email_from_name

        # Enviar email de prueba al administrador
        test_result = test_service.send_email(
            to_email=current_user.email,
            subject=f"🎯 Configuración de email completada - {settings.APP_NAME}",
            html_content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Configuración Completada</title>
        </head>
        <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                    <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 36px;">🎯</span>
                    </div>
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Configuración Completada</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">{settings.APP_NAME}</p>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">¡Hola {current_user.nombre_completo}!</h2>

                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px;">
                        La configuración del servicio de email ha sido completada exitosamente.
                    </p>

                    <!-- Success Box -->
                    <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center; box-shadow: 0 8px 20px rgba(0, 184, 148, 0.15);">
                        <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 28px;">✅</span>
                        </div>
                        <h3 style="color: white; margin: 0 0 15px; font-size: 20px;">¡Servicio de Email Activo!</h3>
                        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                            Los emails del sistema ahora se enviarán correctamente.
                        </p>
                    </div>

                    <!-- Features -->
                    <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); border-left: 4px solid #e17055; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 24px; margin-right: 15px;">📧</span>
                            <div>
                                <h4 style="color: #d63031; margin: 0 0 10px; font-size: 18px;">Emails que se enviarán automáticamente:</h4>
                                <ul style="color: #636e72; margin: 0; padding-left: 20px;">
                                    <li>Cambios de contraseña realizados por administradores</li>
                                    <li>Confirmaciones de solicitudes de cambio de contraseña</li>
                                    <li>Procesamiento de solicitudes (aprobadas/rechazadas)</li>
                                    <li>Notificaciones del sistema</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px; text-align: center;">
                        <p style="color: #999; font-size: 14px; margin: 0;">
                            <strong>{settings.APP_NAME}</strong><br>
                            Sistema de Gestión de Préstamos<br>
                            <span style="color: #ccc;">Configuración de email completada exitosamente</span>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    )

        if test_result:
            return {"message": "Configuración de email guardada y probada exitosamente. Se envió un email de prueba."}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La configuración SMTP no es válida. Verifica los datos e intenta nuevamente."
            )

    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando configuración de email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al guardar la configuración."
        )

@router.post("/email/test")
async def probar_config_email(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Enviar email de prueba con la configuración actual"""
    # Leer configuración desde la base de datos
    email_configs_db = {}
    configuraciones = db.query(ConfiguracionModel).filter(
        ConfiguracionModel.categoria == "email"
    ).all()

    for config in configuraciones:
        if config.clave == "smtp_port":
            email_configs_db[config.clave] = int(config.valor) if config.valor and config.valor.isdigit() else 587
        elif config.clave in ["smtp_use_tls", "smtp_use_ssl"]:
            email_configs_db[config.clave] = config.valor and config.valor.lower() == "true"
        else:
            email_configs_db[config.clave] = config.valor or ""

    # Verificar si está configurado
    is_configured = bool(
        email_configs_db.get("smtp_server") and
        email_configs_db.get("smtp_username") and
        email_configs_db.get("email_from")
    )

    if not is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El servicio de email no está configurado"
        )

    # Crear servicio con configuración de BD
    from app.services.email_service import EmailService
    test_service = EmailService()
    test_service.smtp_server = email_configs_db.get("smtp_server", "")
    test_service.smtp_port = email_configs_db.get("smtp_port", 587)
    test_service.smtp_username = email_configs_db.get("smtp_username", "")
    test_service.smtp_password = email_configs_db.get("smtp_password", "")
    test_service.use_tls = email_configs_db.get("smtp_use_tls", True)
    test_service.use_ssl = email_configs_db.get("smtp_use_ssl", False)
    test_service.email_from = email_configs_db.get("email_from", "")
    test_service.email_from_name = email_configs_db.get("email_from_name", "")

    test_result = test_service.send_email(
        to_email=current_user.email,
        subject=f"🧪 Prueba de email - {settings.APP_NAME}",
        html_content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Prueba de Email</title>
        </head>
        <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 40px 30px; text-align: center;">
                    <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 36px;">🧪</span>
                    </div>
                    <h1 style="color: #333; margin: 0; font-size: 28px; font-weight: 600;">Prueba de Email</h1>
                    <p style="color: #666; margin: 10px 0 0; font-size: 16px;">{settings.APP_NAME}</p>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">¡Hola {current_user.nombre_completo}!</h2>

                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px;">
                        Este es un email de prueba enviado desde el sistema de configuración de {settings.APP_NAME}.
                    </p>

                    <!-- Success Box -->
                    <div style="background: linear-gradient(135deg, #55efc4 0%, #00b894 100%); border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center; box-shadow: 0 8px 20px rgba(0, 184, 148, 0.15);">
                        <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 28px;">✅</span>
                        </div>
                        <h3 style="color: white; margin: 0 0 15px; font-size: 20px;">¡Configuración Exitosa!</h3>
                        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                            Si estás viendo este mensaje, el servicio de email está funcionando correctamente.
                        </p>
                    </div>

                    <!-- Config Info -->
                    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-left: 4px solid #0984e3; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 24px; margin-right: 15px;">📧</span>
                            <div>
                                <h4 style="color: white; margin: 0 0 10px; font-size: 18px;">Configuración SMTP</h4>
                                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                                    Los emails del sistema ahora se enviarán correctamente a través del servidor configurado.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px; text-align: center;">
                        <p style="color: #999; font-size: 14px; margin: 0;">
                            <strong>{settings.APP_NAME}</strong><br>
                            Sistema de Gestión de Préstamos<br>
                            <span style="color: #ccc;">Email de prueba enviado desde la configuración del sistema</span>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    )

    if test_result:
        return {"message": "Email de prueba enviado exitosamente"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el email de prueba. Verifica la configuración SMTP."
        )


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
