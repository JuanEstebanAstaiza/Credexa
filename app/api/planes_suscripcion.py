"""
Endpoints para gestión de Planes de Suscripción SaaS
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_super_admin_user
from app.models.user import Usuario as UsuarioModel
from app.models.plan_suscripcion import PlanSuscripcion
from app.schemas.plan_suscripcion import (
    PlanSuscripcionCreate, PlanSuscripcionUpdate, PlanSuscripcionResponse,
    PlanSuscripcionStats
)

router = APIRouter(
    prefix="/planes-suscripcion",
    tags=["planes de suscripción"],
    responses={404: {"description": "Plan no encontrado"}},
)


@router.post("/", response_model=PlanSuscripcionResponse)
async def crear_plan_suscripcion(
    plan_data: PlanSuscripcionCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Crear un nuevo plan de suscripción (solo super-administradores)
    """
    # Verificar que el slug no esté duplicado
    existing_plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.slug == plan_data.slug).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un plan con este slug"
        )

    # Crear el plan
    db_plan = PlanSuscripcion(**plan_data.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.get("/", response_model=List[PlanSuscripcionResponse])
async def listar_planes_suscripcion(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    activo: Optional[bool] = None,
    popular: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Listar planes de suscripción (solo super-administradores)
    """
    query = db.query(PlanSuscripcion)

    if activo is not None:
        query = query.filter(PlanSuscripcion.activo == activo)
    if popular is not None:
        query = query.filter(PlanSuscripcion.popular == popular)

    planes = query.order_by(PlanSuscripcion.orden, PlanSuscripcion.nombre).offset(skip).limit(limit).all()
    return planes


@router.get("/{plan_id}", response_model=PlanSuscripcionResponse)
async def obtener_plan_suscripcion(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Obtener un plan de suscripción por ID (solo super-administradores)
    """
    plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de suscripción no encontrado"
        )
    return plan


@router.put("/{plan_id}", response_model=PlanSuscripcionResponse)
async def actualizar_plan_suscripcion(
    plan_id: int,
    plan_data: PlanSuscripcionUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Actualizar un plan de suscripción (solo super-administradores)
    """
    plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de suscripción no encontrado"
        )

    # Verificar slug único si se está cambiando
    if plan_data.slug and plan_data.slug != plan.slug:
        existing_plan = db.query(PlanSuscripcion).filter(
            PlanSuscripcion.slug == plan_data.slug,
            PlanSuscripcion.id != plan_id
        ).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un plan con este slug"
            )

    # Aplicar actualizaciones
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
async def eliminar_plan_suscripcion(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Eliminar un plan de suscripción (solo super-administradores)
    """
    plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de suscripción no encontrado"
        )

    # Verificar que no tenga suscripciones activas
    if plan.suscripciones and any(s.estado.value == "activa" for s in plan.suscripciones):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un plan que tiene suscripciones activas"
        )

    db.delete(plan)
    db.commit()

    return {"message": f"Plan '{plan.nombre}' eliminado exitosamente"}


@router.get("/stats/{plan_id}", response_model=PlanSuscripcionStats)
async def estadisticas_plan_suscripcion(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_super_admin_user)
):
    """
    Obtener estadísticas de un plan específico (solo super-administradores)
    """
    plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de suscripción no encontrado"
        )

    from app.models.suscripcion import Suscripcion, EstadoSuscripcion

    # Contar suscripciones activas
    suscripciones_activas = db.query(Suscripcion).filter(
        Suscripcion.plan_id == plan_id,
        Suscripcion.estado == EstadoSuscripcion.ACTIVA
    ).count()

    # Calcular ingresos
    from sqlalchemy import func, extract
    from datetime import datetime

    # Ingresos mensuales (suscripciones mensuales activas)
    ingresos_mensuales = db.query(func.sum(Suscripcion.precio_pagado)).filter(
        Suscripcion.plan_id == plan_id,
        Suscripcion.estado == EstadoSuscripcion.ACTIVA,
        Suscripcion.tipo == "mensual"
    ).scalar() or 0

    # Ingresos anuales (suscripciones anuales activas * 12)
    ingresos_anuales_suscripciones = db.query(func.sum(Suscripcion.precio_pagado)).filter(
        Suscripcion.plan_id == plan_id,
        Suscripcion.estado == EstadoSuscripcion.ACTIVA,
        Suscripcion.tipo == "anual"
    ).scalar() or 0

    return PlanSuscripcionStats(
        plan_id=plan.id,
        plan_nombre=plan.nombre,
        suscripciones_activas=suscripciones_activas,
        ingresos_mensuales=float(ingresos_mensuales),
        ingresos_anuales=float(ingresos_anuales_suscripciones)
    )

