"""
Endpoints de gestión de pagos
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant
from app.models.user import Usuario
from app.models.pago import Pago
from app.models.prestamo import Prestamo
from app.models.socio import Socio
from app.models.pago_socio import PagoSocio
from app.services.documentos_service import DocumentosService
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
    current_user: Usuario = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Registrar un nuevo pago"""
    # Verificar que el préstamo existe, está activo o refinanciado y pertenece a la empresa
    prestamo = db.query(Prestamo).filter(
        Prestamo.id == pago_data.prestamo_id,
        Prestamo.empresa_id == tenant.id
    ).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado o no pertenece a su empresa",
        )

    if prestamo.estado not in ["activo", "refinanciado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden registrar pagos en préstamos inactivos",
        )

    # Calcular desglose del pago (lógica simplificada)
    # En un sistema real, esto sería más complejo considerando amortización
    monto_pagado_float = float(pago_data.monto_pagado)
    valor_cuota_float = float(prestamo.valor_cuota)

    if monto_pagado_float >= valor_cuota_float:
        # Pago completo de cuota
        capital_pagado = valor_cuota_float * 0.7  # 70% capital (aproximado)
        intereses_pagados = valor_cuota_float * 0.3  # 30% intereses (aproximado)
        tipo_pago = "cuota"
        numero_cuota = (prestamo.cuotas_pagadas + 1)
    else:
        # Pago parcial (abono)
        capital_pagado = monto_pagado_float * 0.7  # 70% capital
        intereses_pagados = monto_pagado_float * 0.3  # 30% intereses
        tipo_pago = "abono"
        numero_cuota = None

    # Crear el pago con empresa_id
    db_pago = Pago(
        empresa_id=tenant.id,
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

    # Actualizar el préstamo solo si no es refinanciado con saldo 0
    # Los préstamos refinanciados mantienen saldo 0 para trazabilidad histórica
    if not (prestamo.estado == "refinanciado" and prestamo.saldo_pendiente == 0):
        if tipo_pago == "cuota":
            prestamo.cuotas_pagadas += 1

        prestamo.saldo_pendiente -= pago_data.monto_pagado

        # Verificar si el préstamo está completamente pagado
        if prestamo.saldo_pendiente <= 0:
            prestamo.estado = "pagado"
            prestamo.saldo_pendiente = 0

    # Si el préstamo es de un socio, registrar el movimiento correspondiente
    if prestamo.origen == "socio" and prestamo.socio_id:
        socio = db.query(Socio).filter(Socio.id == prestamo.socio_id).first()
        if socio:
            # Calcular la participación del socio en este pago
            # Para simplificar, asumimos que el socio aporta proporcionalmente
            # En un sistema real, esto podría ser más complejo
            porcentaje_socio = socio.porcentaje_participacion or 100.0  # Por defecto 100%

            # El socio recibe su parte del capital pagado
            monto_socio = (capital_pagado * porcentaje_socio / 100)

            if monto_socio > 0:
                saldo_anterior = socio.capital_actual
                socio.capital_actual = float(socio.capital_actual) + float(monto_socio)
                saldo_nuevo = socio.capital_actual

                # Registrar como "devolucion" (capital devuelto)
                pago_socio = PagoSocio(
                    socio_id=prestamo.socio_id,
                    tipo="devolucion",
                    monto=monto_socio,
                    fecha_pago=pago_data.fecha_pago or datetime.now(),
                    descripcion=f"Cuota #{numero_cuota} del préstamo #{prestamo.id}",
                    prestamo_id=prestamo.id,
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=saldo_nuevo,
                    registrado_por=current_user.id
                )
                db.add(pago_socio)
                db.add(socio)

    db.commit()
    db.refresh(db_pago)

    return db_pago

@router.post("/con-archivos", response_model=PagoSchema)
async def registrar_pago_con_archivos(
    prestamo_id: int = Form(...),
    monto_pagado: float = Form(...),
    fecha_pago: Optional[str] = Form(None),
    metodo_pago: Optional[str] = Form(None),
    referencia_pago: Optional[str] = Form(None),
    observaciones: Optional[str] = Form(None),
    descripcion_archivos: Optional[str] = Form(None),
    archivos: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar un nuevo pago con archivos de soporte opcionales"""
    # Verificar que el préstamo existe y está activo o refinanciado
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    if prestamo.estado not in ["activo", "refinanciado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden registrar pagos en préstamos inactivos",
        )

    # Convertir datos
    from decimal import Decimal
    monto_pagado_decimal = Decimal(str(monto_pagado))
    fecha_pago_datetime = None
    if fecha_pago:
        try:
            fecha_pago_datetime = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00'))
        except:
            fecha_pago_datetime = datetime.now()

    # Calcular desglose del pago (lógica simplificada)
    valor_cuota_float = float(prestamo.valor_cuota)
    monto_pagado_float = float(monto_pagado_decimal)

    if monto_pagado_float >= valor_cuota_float:
        # Pago completo de cuota
        capital_pagado = valor_cuota_float * 0.7  # 70% capital (aproximado)
        intereses_pagados = valor_cuota_float * 0.3  # 30% intereses (aproximado)
        tipo_pago = "cuota"
        numero_cuota = (prestamo.cuotas_pagadas + 1)
    else:
        # Pago parcial (abono)
        capital_pagado = monto_pagado_float * 0.7  # 70% capital
        intereses_pagados = monto_pagado_float * 0.3  # 30% intereses
        tipo_pago = "abono"
        numero_cuota = None

    # Crear el pago
    db_pago = Pago(
        prestamo_id=prestamo_id,
        fecha_pago=fecha_pago_datetime or datetime.now(),
        monto_pagado=monto_pagado_decimal,
        tipo_pago=tipo_pago,
        numero_cuota=numero_cuota,
        capital_pagado=round(capital_pagado, 2),
        intereses_pagados=round(intereses_pagados, 2),
        metodo_pago=metodo_pago,
        referencia_pago=referencia_pago,
        observaciones=observaciones
    )

    db.add(db_pago)
    db.flush()  # Obtener el ID del pago

    # Crear carpeta automática para el pago
    carpeta_pago = DocumentosService.crear_carpeta_pago(
        db, db_pago.id, "cliente", prestamo.cliente_id, prestamo.id
    )

    # Subir archivos si se proporcionaron
    documentos_subidos = []
    if archivos and len(archivos) > 0:
        for archivo in archivos:
            if archivo.filename:  # Solo procesar archivos con nombre
                resultado = DocumentosService.subir_documento_automatico(
                    db, archivo, carpeta_pago.id,
                    tipo_documento="comprobante_pago",
                    descripcion=descripcion_archivos or f"Comprobante de pago #{db_pago.id}",
                    usuario_id=current_user.id
                )
                if resultado:
                    documentos_subidos.append(resultado)

    # Actualizar el préstamo solo si no es refinanciado con saldo 0
    # Los préstamos refinanciados mantienen saldo 0 para trazabilidad histórica
    if not (prestamo.estado == "refinanciado" and prestamo.saldo_pendiente == 0):
        if tipo_pago == "cuota":
            prestamo.cuotas_pagadas += 1

        prestamo.saldo_pendiente -= monto_pagado_decimal

        # Verificar si el préstamo está completamente pagado
        if prestamo.saldo_pendiente <= 0:
            prestamo.estado = "pagado"
            prestamo.saldo_pendiente = 0

    # Si el préstamo es de un socio, registrar el movimiento correspondiente
    if prestamo.origen == "socio" and prestamo.socio_id:
        socio = db.query(Socio).filter(Socio.id == prestamo.socio_id).first()
        if socio:
            # Calcular la participación del socio en este pago
            porcentaje_socio = socio.porcentaje_participacion or 100.0  # Por defecto 100%

            # El socio recibe su parte del capital pagado
            monto_socio = (capital_pagado * porcentaje_socio / 100)

            if monto_socio > 0:
                saldo_anterior = socio.capital_actual
                socio.capital_actual = float(socio.capital_actual) + float(monto_socio)
                saldo_nuevo = socio.capital_actual

                # Registrar como "devolucion" (capital devuelto)
                pago_socio = PagoSocio(
                    socio_id=prestamo.socio_id,
                    tipo="devolucion",
                    monto=monto_socio,
                    fecha_pago=fecha_pago_datetime or datetime.now(),
                    descripcion=f"Cuota #{numero_cuota} del préstamo #{prestamo.id}",
                    prestamo_id=prestamo.id,
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=saldo_nuevo,
                    registrado_por=current_user.id
                )
                db.add(pago_socio)
                db.add(socio)

    db.commit()
    db.refresh(db_pago)

    # Agregar información de documentos subidos a la respuesta
    db_pago.documentos_subidos = documentos_subidos

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
    current_user: Usuario = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Listar pagos con filtros y paginación"""
    # Construir filtros
    filtros = [Pago.empresa_id == tenant.id]

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
    current_user: Usuario = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Obtener un pago por ID con información del préstamo"""
    # Cargar pago con relación al préstamo
    pago = db.query(Pago).options(joinedload(Pago.prestamo)).filter(
        Pago.id == pago_id,
        Pago.empresa_id == tenant.id
    ).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado o no pertenece a su empresa",
        )
    return pago

@router.put("/{pago_id}", response_model=PagoSchema)
async def actualizar_pago(
    pago_id: int,
    pago_data: PagoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Actualizar un pago (solo campos no financieros)"""
    pago = db.query(Pago).filter(
        Pago.id == pago_id,
        Pago.empresa_id == tenant.id
    ).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado o no pertenece a su empresa",
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
    current_user: Usuario = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Eliminar un pago (solo si el préstamo sigue activo)"""
    pago = db.query(Pago).filter(
        Pago.id == pago_id,
        Pago.empresa_id == tenant.id
    ).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado o no pertenece a su empresa",
        )

    # Verificar que el préstamo esté activo y pertenezca a la empresa
    prestamo = db.query(Prestamo).filter(
        Prestamo.id == pago.prestamo_id,
        Prestamo.empresa_id == tenant.id
    ).first()
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
