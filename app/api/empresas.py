"""
API para gestión de empresas (tenants) en arquitectura SaaS
Solo accesible por super-administradores
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
import re

from app.core.database import get_db
from app.models import Empresa, Usuario, Rol
from app.core.security import get_current_super_admin_user, get_password_hash
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate, EmpresaResponse

router = APIRouter(
    tags=["empresas"],
    responses={404: {"description": "Empresa no encontrada"}},
)

@router.post("/", response_model=EmpresaResponse)
async def crear_empresa(
    empresa_data: EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Crear una nueva empresa (tenant) en el sistema SaaS.
    Solo accesible para super-administradores.
    """
    # Validar slug único
    existing_slug = db.query(Empresa).filter(Empresa.slug == empresa_data.slug).first()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slug ya está en uso. Elige otro nombre único."
        )

    # Validar email único
    existing_email = db.query(Empresa).filter(Empresa.email == empresa_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado para otra empresa."
        )

    # Validar dominio único si se proporciona
    if empresa_data.dominio:
        existing_domain = db.query(Empresa).filter(Empresa.dominio == empresa_data.dominio).first()
        if existing_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El dominio ya está en uso."
            )

    # Crear la nueva empresa
    nueva_empresa = Empresa(
        nombre=empresa_data.nombre,
        slug=empresa_data.slug,
        dominio=empresa_data.dominio,
        email=empresa_data.email,
        telefono=empresa_data.telefono,
        direccion=empresa_data.direccion,
        configuracion=empresa_data.configuracion or {},
        activo=True
    )

    db.add(nueva_empresa)
    db.flush()  # Para obtener el ID

    # Crear el rol de admin si no existe
    admin_role = db.query(Rol).filter(Rol.nombre == "admin").first()
    if not admin_role:
        admin_role = Rol(
            nombre="admin",
            descripcion="Administrador del sistema con acceso completo",
            activo=True
        )
        db.add(admin_role)
        db.flush()

    # Crear el rol de digitador si no existe
    digitador_role = db.query(Rol).filter(Rol.nombre == "digitador").first()
    if not digitador_role:
        digitador_role = Rol(
            nombre="digitador",
            descripcion="Usuario con permisos limitados para digitación",
            activo=True
        )
        db.add(digitador_role)
        db.flush()

    # Crear usuario administrador para la nueva empresa
    # Verificar que el username y email del admin no estén duplicados
    existing_username = db.query(Usuario).filter(Usuario.username == empresa_data.admin_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso."
        )

    existing_admin_email = db.query(Usuario).filter(Usuario.email == empresa_data.admin_data.email).first()
    if existing_admin_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado para otro usuario."
        )

    hashed_password = get_password_hash(empresa_data.admin_data.password)

    admin_user = Usuario(
        nombre_completo=empresa_data.admin_data.nombre_completo,
        username=empresa_data.admin_data.username,
        email=empresa_data.admin_data.email,
        hashed_password=hashed_password,
        rol_id=admin_role.id,
        empresa_id=nueva_empresa.id,
        activo=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(nueva_empresa)

    return nueva_empresa

@router.get("/")
async def listar_empresas(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Listar todas las empresas del sistema.
    """
    query = db.query(Empresa)

    if activo is not None:
        query = query.filter(Empresa.activo == activo)

    empresas = query.offset(skip).limit(limit).all()

    # Crear respuesta básica por ahora
    resultado = []
    for empresa in empresas:
        empresa_dict = {
            'id': empresa.id,
            'nombre': empresa.nombre,
            'slug': empresa.slug,
            'email': empresa.email,
            'activo': empresa.activo,
            'suscripcion_activa': False,  # TODO: Implementar lógica de suscripciones
            'plan': None,
            'suscripcion': None,
            'num_usuarios': 0  # TODO: Implementar conteo de usuarios
        }
        resultado.append(empresa_dict)

    return resultado

@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obtener_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Obtener detalles de una empresa específica.
    Solo accesible para super-administradores.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    return empresa

@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def actualizar_empresa(
    empresa_id: int,
    empresa_update: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Actualizar información de una empresa.
    Solo accesible para super-administradores.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    # Validar slug único (excepto el actual)
    if empresa_update.slug and empresa_update.slug != empresa.slug:
        existing_slug = db.query(Empresa).filter(
            Empresa.slug == empresa_update.slug,
            Empresa.id != empresa_id
        ).first()
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El slug ya está en uso."
            )

    # Validar email único (excepto el actual)
    if empresa_update.email and empresa_update.email != empresa.email:
        existing_email = db.query(Empresa).filter(
            Empresa.email == empresa_update.email,
            Empresa.id != empresa_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso."
            )

    # Validar dominio único (excepto el actual)
    if empresa_update.dominio and empresa_update.dominio != empresa.dominio:
        existing_domain = db.query(Empresa).filter(
            Empresa.dominio == empresa_update.dominio,
            Empresa.id != empresa_id
        ).first()
        if existing_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El dominio ya está en uso."
            )

    # Actualizar campos
    for field, value in empresa_update.dict(exclude_unset=True).items():
        if field == "configuracion" and value is not None:
            # Merge configuración existente con nueva
            existing_config = empresa.configuracion or {}
            existing_config.update(value)
            setattr(empresa, field, existing_config)
        else:
            setattr(empresa, field, value)

    db.commit()
    db.refresh(empresa)
    return empresa

@router.delete("/{empresa_id}")
async def eliminar_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Eliminar una empresa y todos sus datos asociados.
    Operación destructiva - usar con precaución.
    Solo accesible para super-administradores.
    """
    # No permitir eliminar la empresa por defecto (ID=1)
    if empresa_id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la empresa por defecto del sistema."
        )

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    # Eliminar la empresa (las relaciones con cascade harán el resto)
    db.delete(empresa)
    db.commit()

    return {"message": f"Empresa '{empresa.nombre}' eliminada exitosamente"}

@router.post("/{empresa_id}/activar")
async def activar_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Activar una empresa suspendida.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    empresa.activo = True
    db.commit()

    return {"message": f"Empresa '{empresa.nombre}' activada exitosamente"}

@router.post("/{empresa_id}/suspender")
async def suspender_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Suspender una empresa (desactivar temporalmente).
    """
    # No permitir suspender la empresa por defecto (ID=1)
    if empresa_id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede suspender la empresa por defecto del sistema."
        )

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    empresa.activo = False
    db.commit()

    return {"message": f"Empresa '{empresa.nombre}' suspendida exitosamente"}

@router.get("/{empresa_id}/estadisticas")
async def estadisticas_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_super_admin_user)
):
    """
    Obtener estadísticas generales de una empresa.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    # Contar usuarios activos
    usuarios_activos = db.query(Usuario).filter(
        Usuario.empresa_id == empresa_id,
        Usuario.activo == True
    ).count()

    # Contar clientes
    total_clientes = db.query(Cliente).filter(Cliente.empresa_id == empresa_id).count()

    # Contar préstamos
    total_prestamos = db.query(Prestamo).filter(Prestamo.empresa_id == empresa_id).count()

    # Contar préstamos activos
    prestamos_activos = db.query(Prestamo).filter(
        Prestamo.empresa_id == empresa_id,
        Prestamo.estado == "activo"
    ).count()

    # Calcular total cartera
    from sqlalchemy import func as sql_func
    total_cartera = db.query(sql_func.sum(Prestamo.monto)).filter(
        Prestamo.empresa_id == empresa_id,
        Prestamo.estado.in_(["activo", "mora"])
    ).scalar() or 0

    return {
        "empresa": empresa.nombre,
        "usuarios_activos": usuarios_activos,
        "total_clientes": total_clientes,
        "total_prestamos": total_prestamos,
        "prestamos_activos": prestamos_activos,
        "total_cartera": float(total_cartera),
        "activo": empresa.activo
    }
