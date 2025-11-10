"""
Endpoints para gestión de Suscripciones SaaS
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_super_admin_user
from app.models.user import Usuario as UsuarioModel
from app.models.suscripcion import Suscripcion, EstadoSuscripcion, TipoSuscripcion
from app.models.empresa import Empresa
from app.models.plan_suscripcion import PlanSuscripcion
from app.schemas.suscripcion import (
    SuscripcionCreate, SuscripcionUpdate, SuscripcionResponse,
    SuscripcionDetalleResponse, SuscripcionEstadisticas
)

router = APIRouter(
    prefix="/suscripciones",
    tags=["suscripciones"],
    responses={404: {"description": "Suscripción no encontrada"}},
)


@router.post("/", response_model=SuscripcionResponse)
async def crear_suscripcion(
    suscripcion_data: SuscripcionCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Crear una nueva suscripción (solo super-administradores)
    """
    # Verificar que la empresa existe
    empresa = db.query(Empresa).filter(Empresa.id == suscripcion_data.empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    # Verificar que el plan existe y está activo
    plan = db.query(PlanSuscripcion).filter(
        PlanSuscripcion.id == suscripcion_data.plan_id,
        PlanSuscripcion.activo == True
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de suscripción no encontrado o inactivo"
        )

    # Verificar que no exista una suscripción activa para esta empresa
    suscripcion_activa = db.query(Suscripcion).filter(
        Suscripcion.empresa_id == suscripcion_data.empresa_id,
        Suscripcion.estado == "activa"
    ).first()
    if suscripcion_activa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La empresa ya tiene una suscripción activa"
        )

    # Calcular fecha de fin si no se proporciona
    fecha_inicio = suscripcion_data.fecha_inicio or datetime.now()
    fecha_fin = suscripcion_data.fecha_fin

    if not fecha_fin:
        if suscripcion_data.tipo == "mensual":
            fecha_fin = fecha_inicio + timedelta(days=30)
        else:  # ANUAL
            fecha_fin = fecha_inicio + timedelta(days=365)

    # Crear la suscripción de manera simple
    try:
        db_suscripcion = Suscripcion(
            empresa_id=suscripcion_data.empresa_id,
            plan_id=suscripcion_data.plan_id,
            estado=suscripcion_data.estado,
            tipo=suscripcion_data.tipo,
            precio_pagado=suscripcion_data.precio_pagado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        db.add(db_suscripcion)
        db.commit()
        db.refresh(db_suscripcion)

        return db_suscripcion
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear suscripción: {str(e)}"
        )


@router.get("/")
async def listar_suscripciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    empresa_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    estado: Optional[EstadoSuscripcion] = None,
    tipo: Optional[TipoSuscripcion] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Listar suscripciones con filtros (solo super-administradores)
    """
    query = db.query(Suscripcion)

    if empresa_id:
        query = query.filter(Suscripcion.empresa_id == empresa_id)
    if plan_id:
        query = query.filter(Suscripcion.plan_id == plan_id)
    if estado:
        query = query.filter(Suscripcion.estado == estado)
    if tipo:
        query = query.filter(Suscripcion.tipo == tipo)

    suscripciones = query.order_by(Suscripcion.fecha_creacion.desc()).offset(skip).limit(limit).all()

    # Obtener IDs únicos de empresas y planes para queries eficientes
    empresa_ids = {s.empresa_id for s in suscripciones if s.empresa_id}
    plan_ids = {s.plan_id for s in suscripciones if s.plan_id}

    # Cargar empresas y planes en bulk
    empresas = {}
    if empresa_ids:
        empresas_query = db.query(Empresa).filter(Empresa.id.in_(empresa_ids)).all()
        empresas = {e.id: e for e in empresas_query}

    planes = {}
    if plan_ids:
        planes_query = db.query(PlanSuscripcion).filter(PlanSuscripcion.id.in_(plan_ids)).all()
        planes = {p.id: p for p in planes_query}

    # Convertir a formato JSON serializable
    result = []
    for s in suscripciones:
        empresa = empresas.get(s.empresa_id)
        plan = planes.get(s.plan_id)

        item = {
            'id': s.id,
            'empresa_id': s.empresa_id,
            'plan_id': s.plan_id,
            'estado': s.estado,
            'tipo': s.tipo,
            'precio_pagado': float(s.precio_pagado) if s.precio_pagado is not None else 0.0,
            'metodo_pago': s.metodo_pago,
            'referencia_pago': s.referencia_pago,
            'renovacion_automatica': s.renovacion_automatica,
            'limite_usuarios': s.limite_usuarios,
            'limite_clientes': s.limite_clientes,
            'limite_prestamos': s.limite_prestamos,
            'limite_almacenamiento_gb': s.limite_almacenamiento_gb,
            'observaciones': s.observaciones,
            'fecha_inicio': s.fecha_inicio.isoformat() if s.fecha_inicio else None,
            'fecha_fin': s.fecha_fin.isoformat() if s.fecha_fin else None,
            'fecha_cancelacion': s.fecha_cancelacion.isoformat() if s.fecha_cancelacion else None,
            'fecha_suspension': s.fecha_suspension.isoformat() if s.fecha_suspension else None,
            'fecha_creacion': s.fecha_creacion.isoformat() if s.fecha_creacion else None,
            'fecha_actualizacion': s.fecha_actualizacion.isoformat() if s.fecha_actualizacion else None,
            # Información de relaciones
            'empresa': {
                'id': empresa.id,
                'nombre': empresa.nombre,
                'email': empresa.email,
                'slug': empresa.slug
            } if empresa else None,
            'plan': {
                'id': plan.id,
                'nombre': plan.nombre,
                'slug': plan.slug,
                'precio_mensual': plan.precio_mensual,
                'precio_anual': plan.precio_anual
            } if plan else None
        }
        result.append(item)

    return result


@router.get("/{suscripcion_id}", response_model=SuscripcionDetalleResponse)
async def obtener_suscripcion(
    suscripcion_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Obtener una suscripción por ID con detalles completos (solo super-administradores)
    """
    suscripcion = db.query(Suscripcion).filter(Suscripcion.id == suscripcion_id).first()

    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    # Cargar empresa y plan por separado
    empresa = None
    if suscripcion.empresa_id:
        empresa = db.query(Empresa).filter(Empresa.id == suscripcion.empresa_id).first()

    plan = None
    if suscripcion.plan_id:
        plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.id == suscripcion.plan_id).first()

    # Crear respuesta
    response = {
        'id': suscripcion.id,
        'empresa_id': suscripcion.empresa_id,
        'plan_id': suscripcion.plan_id,
        'estado': suscripcion.estado,
        'tipo': suscripcion.tipo,
        'precio_pagado': float(suscripcion.precio_pagado) if suscripcion.precio_pagado is not None else 0.0,
        'metodo_pago': suscripcion.metodo_pago,
        'referencia_pago': suscripcion.referencia_pago,
        'renovacion_automatica': suscripcion.renovacion_automatica,
        'limite_usuarios': suscripcion.limite_usuarios,
        'limite_clientes': suscripcion.limite_clientes,
        'limite_prestamos': suscripcion.limite_prestamos,
        'limite_almacenamiento_gb': suscripcion.limite_almacenamiento_gb,
        'observaciones': suscripcion.observaciones,
        'fecha_inicio': suscripcion.fecha_inicio.isoformat() if suscripcion.fecha_inicio else None,
        'fecha_fin': suscripcion.fecha_fin.isoformat() if suscripcion.fecha_fin else None,
        'fecha_cancelacion': suscripcion.fecha_cancelacion.isoformat() if suscripcion.fecha_cancelacion else None,
        'fecha_suspension': suscripcion.fecha_suspension.isoformat() if suscripcion.fecha_suspension else None,
        'fecha_creacion': suscripcion.fecha_creacion.isoformat() if suscripcion.fecha_creacion else None,
        'fecha_actualizacion': suscripcion.fecha_actualizacion.isoformat() if suscripcion.fecha_actualizacion else None,
        'empresa': {
            "id": empresa.id,
            "nombre": empresa.nombre,
            "slug": empresa.slug,
            "email": empresa.email,
            "activo": empresa.activo
        } if empresa else None,
        'plan': {
            "id": plan.id,
            "nombre": plan.nombre,
            "precio_mensual": plan.precio_mensual,
            "precio_anual": plan.precio_anual,
            "activo": plan.activo
        } if plan else None
    }

    # Propiedades calculadas
    response['esta_activa'] = suscripcion.esta_activa
    response['dias_restantes'] = suscripcion.dias_restantes

    return response


@router.put("/{suscripcion_id}", response_model=SuscripcionResponse)
async def actualizar_suscripcion(
    suscripcion_id: int,
    suscripcion_data: SuscripcionUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Actualizar una suscripción (solo super-administradores)
    """
    suscripcion = db.query(Suscripcion).filter(Suscripcion.id == suscripcion_id).first()

    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    # Aplicar actualizaciones
    update_data = suscripcion_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(suscripcion, field, value)

    # Si se cambia el estado, actualizar fechas correspondientes
    if 'estado' in update_data:
        if update_data['estado'] == EstadoSuscripcion.CANCELADA:
            suscripcion.fecha_cancelacion = datetime.now()
        elif update_data['estado'] == EstadoSuscripcion.SUSPENDIDA:
            suscripcion.fecha_suspension = datetime.now()

    db.commit()
    db.refresh(suscripcion)

    # Crear respuesta con información adicional
    response = SuscripcionResponse.from_orm(suscripcion)
    response.empresa_nombre = suscripcion.empresa.nombre if suscripcion.empresa else None
    response.plan_nombre = suscripcion.plan.nombre if suscripcion.plan else None

    return response


@router.delete("/{suscripcion_id}")
async def eliminar_suscripcion(
    suscripcion_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Eliminar una suscripción (solo super-administradores)
    """
    suscripcion = db.query(Suscripcion).filter(Suscripcion.id == suscripcion_id).first()
    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    db.delete(suscripcion)
    db.commit()

    return {"message": f"Suscripción eliminada exitosamente"}


@router.post("/{suscripcion_id}/renovar")
async def renovar_suscripcion(
    suscripcion_id: int,
    meses: Optional[int] = 1,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Renovar una suscripción por meses adicionales (solo super-administradores)
    """
    suscripcion = db.query(Suscripcion).filter(Suscripcion.id == suscripcion_id).first()
    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    # Extender la fecha de fin
    if suscripcion.fecha_fin:
        if suscripcion.tipo == TipoSuscripcion.MENSUAL:
            suscripcion.fecha_fin = suscripcion.fecha_fin + timedelta(days=30 * meses)
        else:  # ANUAL
            suscripcion.fecha_fin = suscripcion.fecha_fin + timedelta(days=365 * meses)
    else:
        # Si no tiene fecha fin, calcular desde ahora
        if suscripcion.tipo == TipoSuscripcion.MENSUAL:
            suscripcion.fecha_fin = datetime.now() + timedelta(days=30 * meses)
        else:
            suscripcion.fecha_fin = datetime.now() + timedelta(days=365 * meses)

    db.commit()
    db.refresh(suscripcion)

    return {
        "message": f"Suscripción renovada por {meses} meses",
        "nueva_fecha_fin": suscripcion.fecha_fin.isoformat()
    }


@router.get("/stats/general", response_model=SuscripcionEstadisticas)
async def estadisticas_suscripciones(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Obtener estadísticas generales de suscripciones (solo super-administradores)
    """
    from sqlalchemy import func, extract

    # Conteos por estado
    total_suscripciones = db.query(func.count(Suscripcion.id)).scalar()

    suscripciones_activas = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA
    ).scalar()

    suscripciones_inactivas = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.INACTIVA
    ).scalar()

    suscripciones_suspendidas = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.SUSPENDIDA
    ).scalar()

    suscripciones_canceladas = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.CANCELADA
    ).scalar()

    suscripciones_vencidas = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.VENCIDA
    ).scalar()

    # Ingresos
    ingresos_mensuales_actuales = db.query(func.sum(Suscripcion.precio_pagado)).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA,
        Suscripcion.tipo == TipoSuscripcion.MENSUAL
    ).scalar() or 0

    ingresos_anuales_suscripciones = db.query(func.sum(Suscripcion.precio_pagado)).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA,
        Suscripcion.tipo == TipoSuscripcion.ANUAL
    ).scalar() or 0

    # Promedio de precio
    promedio_precio = db.query(func.avg(Suscripcion.precio_pagado)).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA
    ).scalar() or 0

    # Conteos por tipo
    suscripciones_mensuales = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA,
        Suscripcion.tipo == TipoSuscripcion.MENSUAL
    ).scalar()

    suscripciones_anuales = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.estado == EstadoSuscripcion.ACTIVA,
        Suscripcion.tipo == TipoSuscripcion.ANUAL
    ).scalar()

    # Nuevas suscripciones este mes
    from datetime import datetime
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    nuevas_suscripciones_mes = db.query(func.count(Suscripcion.id)).filter(
        Suscripcion.fecha_creacion >= inicio_mes
    ).scalar()

    return SuscripcionEstadisticas(
        total_suscripciones=total_suscripciones,
        suscripciones_activas=suscripciones_activas,
        suscripciones_inactivas=suscripciones_inactivas,
        suscripciones_suspendidas=suscripciones_suspendidas,
        suscripciones_canceladas=suscripciones_canceladas,
        suscripciones_vencidas=suscripciones_vencidas,
        ingresos_mensuales_actuales=float(ingresos_mensuales_actuales),
        ingresos_anuales_estimados=float(ingresos_anuales_suscripciones),
        promedio_precio_suscripcion=float(promedio_precio),
        suscripciones_mensuales=suscripciones_mensuales,
        suscripciones_anuales=suscripciones_anuales,
        nuevas_suscripciones_mes=nuevas_suscripciones_mes
    )

