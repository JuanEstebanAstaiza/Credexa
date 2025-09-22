"""
Endpoints de gestión de pagos
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import Usuario
from app.models.pago import Pago
from app.models.prestamo import Prestamo
from app.schemas.pago import (
    Pago as PagoSchema, PagoCreate, PagoUpdate,
    PagoFiltro, PagoPaginado, PagoRegistro
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Endpoints API REST

@router.post("", response_model=PagoSchema)
async def registrar_pago(
    pago_data: PagoRegistro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar un nuevo pago"""
    # Verificar que el préstamo existe y está activo
    prestamo = db.query(Prestamo).filter(Prestamo.id == pago_data.prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    if prestamo.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden registrar pagos en préstamos inactivos",
        )

    # Calcular desglose del pago (lógica simplificada)
    # En un sistema real, esto sería más complejo considerando amortización
    if pago_data.monto_pagado >= prestamo.valor_cuota:
        # Pago completo de cuota
        capital_pagado = prestamo.valor_cuota * 0.7  # 70% capital (aproximado)
        intereses_pagados = prestamo.valor_cuota * 0.3  # 30% intereses (aproximado)
        tipo_pago = "cuota"
        numero_cuota = (prestamo.cuotas_pagadas + 1)
    else:
        # Pago parcial (abono)
        capital_pagado = pago_data.monto_pagado * 0.7  # 70% capital
        intereses_pagados = pago_data.monto_pagado * 0.3  # 30% intereses
        tipo_pago = "abono"
        numero_cuota = None

    # Crear el pago
    db_pago = Pago(
        prestamo_id=pago_data.prestamo_id,
        fecha_pago=pago_data.fecha_pago or datetime.now(),
        monto_pagado=pago_data.monto_pagado,
        tipo_pago=tipo_pago,
        numero_cuota=numero_cuota,
        capital_pagado=round(capital_pagado, 2),
        intereses_pagados=round(intereses_pagados, 2),
        metodo_pago=pago_data.metodo_pago,
        referencia_pago=pago_data.referencia_pago,
        observaciones=pago_data.observaciones
    )

    db.add(db_pago)

    # Actualizar el préstamo
    if tipo_pago == "cuota":
        prestamo.cuotas_pagadas += 1

    prestamo.saldo_pendiente -= pago_data.monto_pagado

    # Verificar si el préstamo está completamente pagado
    if prestamo.saldo_pendiente <= 0:
        prestamo.estado = "pagado"
        prestamo.saldo_pendiente = 0

    db.commit()
    db.refresh(db_pago)

    return db_pago

@router.get("", response_model=PagoPaginado)
async def listar_pagos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    prestamo_id: Optional[int] = None,
    tipo_pago: Optional[str] = None,
    metodo_pago: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    monto_min: Optional[float] = None,
    monto_max: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar pagos con filtros y paginación"""
    # Construir filtros
    filtros = []

    if prestamo_id:
        filtros.append(Pago.prestamo_id == prestamo_id)
    if tipo_pago:
        filtros.append(Pago.tipo_pago == tipo_pago)
    if metodo_pago:
        filtros.append(Pago.metodo_pago == metodo_pago)
    if fecha_desde:
        filtros.append(Pago.fecha_pago >= fecha_desde)
    if fecha_hasta:
        filtros.append(Pago.fecha_pago <= fecha_hasta)
    if monto_min:
        filtros.append(Pago.monto_pagado >= monto_min)
    if monto_max:
        filtros.append(Pago.monto_pagado <= monto_max)

    # Consulta base
    query = db.query(Pago)

    # Aplicar filtros
    if filtros:
        query = query.filter(and_(*filtros))

    # Obtener total
    total = query.count()

    # Aplicar paginación y ordenar por fecha descendente
    pagos = query.order_by(Pago.fecha_pago.desc()).offset(skip).limit(limit).all()

    # Calcular páginas
    paginas_totales = (total + limit - 1) // limit if total > 0 else 1
    pagina_actual = (skip // limit) + 1

    return PagoPaginado(
        items=pagos,
        total=total,
        pagina=pagina_actual,
        por_pagina=limit,
        paginas_totales=paginas_totales
    )

@router.get("/{pago_id}", response_model=PagoSchema)
async def obtener_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un pago por ID con información del préstamo"""
    # Cargar pago con relación al préstamo
    pago = db.query(Pago).options(joinedload(Pago.prestamo)).filter(Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado",
        )
    return pago

@router.put("/{pago_id}", response_model=PagoSchema)
async def actualizar_pago(
    pago_id: int,
    pago_data: PagoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un pago (solo campos no financieros)"""
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado",
        )

    # Solo permitir actualizar campos no financieros
    campos_permitidos = ["metodo_pago", "referencia_pago", "observaciones"]

    # Aplicar solo campos permitidos
    update_data = {}
    for campo in campos_permitidos:
        if hasattr(pago_data, campo) and getattr(pago_data, campo) is not None:
            update_data[campo] = getattr(pago_data, campo)

    if update_data:
        for field, value in update_data.items():
            setattr(pago, field, value)

        db.commit()
        db.refresh(pago)

    return pago

@router.delete("/{pago_id}")
async def eliminar_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un pago (solo si el préstamo sigue activo)"""
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado",
        )

    # Verificar que el préstamo esté activo
    prestamo = db.query(Prestamo).filter(Prestamo.id == pago.prestamo_id).first()
    if prestamo.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden eliminar pagos de préstamos inactivos",
        )

    # Revertir los cambios en el préstamo
    prestamo.saldo_pendiente += pago.monto_pagado
    if pago.tipo_pago == "cuota":
        prestamo.cuotas_pagadas -= 1

    # Si el préstamo estaba pagado, volverlo a activo
    if prestamo.saldo_pendiente > 0 and prestamo.estado == "pagado":
        prestamo.estado = "activo"

    db.delete(pago)
    db.commit()

    return {"message": "Pago eliminado exitosamente"}

# Endpoints para páginas HTML

@router.get("/lista", response_class=HTMLResponse)
async def pagina_lista_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de listado de pagos"""
    return templates.TemplateResponse("pagos/lista.html", {
        "request": request,
        "title": "Lista de Pagos",
        "user": current_user
    })

@router.get("/registrar", response_class=HTMLResponse)
async def pagina_registrar_pago(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de registro de pago"""
    from app.models.prestamo import Prestamo
    # Obtener préstamos activos para el select
    prestamos = db.query(Prestamo).filter(Prestamo.estado == "activo").order_by(Prestamo.fecha_inicio.desc()).all()

    return templates.TemplateResponse("pagos/registrar.html", {
        "request": request,
        "title": "Registrar Pago",
        "user": current_user,
        "prestamos": prestamos
    })
