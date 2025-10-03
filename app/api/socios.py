"""
Endpoints de gestión de Socios
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form, File, UploadFile, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.socio import Socio
from app.models.pago_socio import PagoSocio
from app.models.user import Usuario as UsuarioModel
from app.services.documentos_service import DocumentosService
from app.schemas.socio import (
    Socio as SocioSchema,
    SocioCreate,
    SocioUpdate,
    SocioDetalle,
    SocioFiltro
)
from app.schemas.pago_socio import (
    PagoSocio as PagoSocioSchema,
    PagoSocioCreate,
    PagoSocioDetalle,
    PagoSocioFiltro,
    PagoSocioEstadistico
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ========== ENDPOINTS DE SOCIOS ==========

@router.post("", response_model=SocioSchema)
async def crear_socio(
    socio: SocioCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Crear un nuevo socio (solo administradores)"""
    # Verificar que la cédula no esté duplicada
    db_socio = db.query(Socio).filter(Socio.cedula == socio.cedula).first()
    if db_socio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un socio con esta cédula"
        )

    # Crear el socio
    db_socio = Socio(**socio.model_dump())
    db.add(db_socio)
    db.commit()
    db.refresh(db_socio)
    return db_socio


@router.get("", response_model=List[SocioSchema])
async def listar_socios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    filtro: Optional[SocioFiltro] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Listar socios con filtros opcionales"""
    # Endpoint simplificado para debugging
    try:
        # Solo devolver socios básicos sin filtros por ahora
        socios = db.query(Socio).limit(10).all()

        # Convertir manualmente para evitar problemas de Pydantic
        result = []
        for socio in socios:
            result.append({
                "id": socio.id,
                "nombre_completo": socio.nombre_completo,
                "cedula": socio.cedula,
                "telefono": socio.telefono,
                "email": socio.email,
                "direccion": socio.direccion,
                "fecha_nacimiento": socio.fecha_nacimiento,
                "ocupacion": socio.ocupacion,
                "ingresos_mensuales": socio.ingresos_mensuales,
                "referencias_personales": socio.referencias_personales,
                "activo": socio.activo,
                "notas": socio.notas,
                "capital_inicial": float(socio.capital_inicial),
                "capital_actual": float(socio.capital_actual),
                "porcentaje_participacion": float(socio.porcentaje_participacion),
                "creado_en": socio.creado_en,
                "actualizado_en": socio.actualizado_en
            })

        return result
    except Exception as e:
        print(f"Error en listar_socios: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/{socio_id}", response_model=SocioDetalle)
async def obtener_socio(
    socio_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Obtener detalles de un socio específico"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    # Calcular estadísticas
    from app.models.prestamo import Prestamo

    prestamos_activos = db.query(func.count(Prestamo.id)).filter(
        Prestamo.socio_id == socio_id,
        Prestamo.estado == "activo"
    ).scalar() or 0

    prestamos_pagados = db.query(func.count(Prestamo.id)).filter(
        Prestamo.socio_id == socio_id,
        Prestamo.estado == "pagado"
    ).scalar() or 0

    # Pagos recientes (últimos 5)
    pagos_recientes = db.query(PagoSocio).filter(
        PagoSocio.socio_id == socio_id
    ).order_by(PagoSocio.fecha_pago.desc()).limit(5).all()

    pagos_recientes_data = [
        {
            "id": pago.id,
            "tipo": pago.tipo,
            "monto": float(pago.monto),
            "fecha": pago.fecha_pago.isoformat(),
            "descripcion": pago.descripcion
        } for pago in pagos_recientes
    ]

    # Calcular estadísticas manualmente para evitar problemas con propiedades calculadas
    capital_disponible = float(socio.capital_actual) - sum(float(pago.monto) for pago in socio.pagos_socio if pago.tipo == "prestamo")
    total_invertido = sum(float(pago.monto) for pago in socio.pagos_socio if pago.tipo == "prestamo")

    socio_dict = socio.__dict__.copy()
    socio_dict.update({
        "capital_disponible": capital_disponible,
        "total_invertido": total_invertido,
        "prestamos_activos": prestamos_activos,
        "prestamos_pagados": prestamos_pagados,
        "pagos_recientes": pagos_recientes_data
    })

    return SocioDetalle(**socio_dict)


@router.put("/{socio_id}", response_model=SocioSchema)
async def actualizar_socio(
    socio_id: int,
    socio_update: SocioUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Actualizar un socio (solo administradores)"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    # Verificar cédula duplicada si se está cambiando
    if socio_update.cedula and socio_update.cedula != socio.cedula:
        db_socio = db.query(Socio).filter(Socio.cedula == socio_update.cedula).first()
        if db_socio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un socio con esta cédula"
            )

    # Actualizar campos
    update_data = socio_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(socio, field, value)

    db.commit()
    db.refresh(socio)
    return socio


@router.delete("/{socio_id}")
async def eliminar_socio(
    socio_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Eliminar un socio (solo administradores)"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    # Verificar que no tenga préstamos activos
    prestamos_activos = db.query(Socio).join(Socio.prestamos).filter(
        Socio.id == socio_id,
        Socio.prestamos.any(and_(Socio.prestamos.c.estado == "activo"))
    ).first()

    if prestamos_activos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un socio con préstamos activos"
        )

    db.delete(socio)
    db.commit()
    return {"message": "Socio eliminado exitosamente"}


# ========== ENDPOINTS DE PAGOS DE SOCIO ==========

@router.post("/{socio_id}/pagos", response_model=PagoSocioSchema)
async def registrar_pago_socio(
    socio_id: int,
    pago: PagoSocioCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Registrar un pago para un socio (administradores y socios para retiros)"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    # Verificar que el pago pertenece al socio correcto
    if pago.socio_id != socio_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El socio_id del pago no coincide con el socio especificado"
        )

    # Verificar número de recibo único si se proporciona
    if pago.numero_recibo:
        db_pago = db.query(PagoSocio).filter(PagoSocio.numero_recibo == pago.numero_recibo).first()
        if db_pago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un pago con este número de recibo"
            )

    # Verificar permisos por tipo de pago
    tipos_admin = ['aporte', 'devolucion', 'ganancia', 'retiro']
    if pago.tipo in tipos_admin and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo administradores pueden registrar pagos de tipo '{pago.tipo}'"
        )

    # Calcular saldos
    saldo_anterior = socio.capital_actual
    if pago.tipo in ['aporte', 'prestamo']:
        saldo_nuevo = saldo_anterior + pago.monto
    else:  # devolucion, ganancia, retiro
        saldo_nuevo = saldo_anterior - pago.monto

    # Verificar que no se retire más de lo disponible
    if pago.tipo in ['devolucion', 'ganancia', 'retiro'] and saldo_nuevo < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay suficiente capital disponible para esta operación"
        )

    # Crear el pago
    db_pago = PagoSocio(
        **pago.model_dump(),
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        registrado_por=current_user.id
    )

    db.add(db_pago)

    # Actualizar capital del socio
    socio.capital_actual = saldo_nuevo

    db.commit()
    db.refresh(db_pago)
    return db_pago

@router.post("/{socio_id}/pagos/con-archivos", response_model=PagoSocioSchema)
async def registrar_pago_socio_con_archivos(
    socio_id: int = Path(...),
    tipo: str = Form(...),
    monto: float = Form(...),
    fecha_pago: Optional[str] = Form(None),
    metodo_pago: Optional[str] = Form(None),
    numero_recibo: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    descripcion_archivos: Optional[str] = Form(None),
    archivos: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Registrar un pago para un socio con archivos de soporte opcionales"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    # Convertir datos
    from decimal import Decimal
    monto_decimal = Decimal(str(monto))
    fecha_pago_datetime = None
    if fecha_pago:
        try:
            fecha_pago_datetime = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00'))
        except:
            fecha_pago_datetime = datetime.now()

    # Verificar número de recibo único si se proporciona
    if numero_recibo:
        db_pago = db.query(PagoSocio).filter(PagoSocio.numero_recibo == numero_recibo).first()
        if db_pago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un pago con este número de recibo"
            )

    # Verificar permisos por tipo de pago
    tipos_admin = ['aporte', 'devolucion', 'ganancia', 'retiro']
    if tipo in tipos_admin and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo administradores pueden registrar pagos de tipo '{tipo}'"
        )

    # Calcular saldos
    saldo_anterior = socio.capital_actual
    if tipo in ['aporte', 'prestamo']:
        saldo_nuevo = saldo_anterior + monto_decimal
    else:  # devolucion, ganancia, retiro
        saldo_nuevo = saldo_anterior - monto_decimal

    # Verificar que no se retire más de lo disponible
    if tipo in ['devolucion', 'ganancia', 'retiro'] and saldo_nuevo < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay suficiente capital disponible para esta operación"
        )

    # Crear el pago
    db_pago = PagoSocio(
        socio_id=socio_id,
        tipo=tipo,
        monto=monto_decimal,
        fecha_pago=fecha_pago_datetime or datetime.now(),
        metodo_pago=metodo_pago,
        numero_recibo=numero_recibo,
        descripcion=descripcion,
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        registrado_por=current_user.id
    )

    db.add(db_pago)
    db.flush()  # Obtener el ID del pago

    # Crear carpeta automática para el pago
    carpeta_pago = DocumentosService.crear_carpeta_pago(
        db, db_pago.id, "socio", socio_id
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

    # Actualizar capital del socio
    socio.capital_actual = saldo_nuevo

    db.commit()
    db.refresh(db_pago)

    # Agregar información de documentos subidos a la respuesta
    db_pago.documentos_subidos = documentos_subidos

    return db_pago


@router.get("/{socio_id}/pagos", response_model=List[PagoSocioDetalle])
async def listar_pagos_socio(
    socio_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    filtro: Optional[PagoSocioFiltro] = None,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Listar pagos de un socio específico"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    query = db.query(PagoSocio).options(
        joinedload(PagoSocio.usuario)
    ).filter(PagoSocio.socio_id == socio_id)

    if filtro:
        if filtro.tipo:
            query = query.filter(PagoSocio.tipo == filtro.tipo)
        if filtro.fecha_desde:
            query = query.filter(PagoSocio.fecha_pago >= filtro.fecha_desde)
        if filtro.fecha_hasta:
            query = query.filter(PagoSocio.fecha_pago <= filtro.fecha_hasta)
        if filtro.monto_min:
            query = query.filter(PagoSocio.monto >= filtro.monto_min)
        if filtro.monto_max:
            query = query.filter(PagoSocio.monto <= filtro.monto_max)
        if filtro.metodo_pago:
            query = query.filter(PagoSocio.metodo_pago == filtro.metodo_pago)

    query = query.order_by(PagoSocio.fecha_pago.desc())
    pagos = query.offset(skip).limit(limit).all()

    # Convertir a formato detallado
    pagos_detalle = []
    for pago in pagos:
        pago_dict = pago.__dict__.copy()
        pago_dict.update({
            "socio_nombre": socio.nombre_completo,
            "usuario_registro": pago.usuario.nombre_completo if pago.usuario else None
        })
        pagos_detalle.append(PagoSocioDetalle(**pago_dict))

    return pagos_detalle


@router.get("/{socio_id}/pagos/{pago_id}", response_model=PagoSocioDetalle)
async def obtener_pago_socio(
    socio_id: int,
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Obtener detalles de un pago específico de un socio"""
    pago = db.query(PagoSocio).options(
        joinedload(PagoSocio.usuario),
        joinedload(PagoSocio.socio)
    ).filter(
        PagoSocio.id == pago_id,
        PagoSocio.socio_id == socio_id
    ).first()

    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )

    pago_dict = pago.__dict__.copy()
    pago_dict.update({
        "socio_nombre": pago.socio.nombre_completo,
        "usuario_registro": pago.usuario.nombre_completo if pago.usuario else None
    })

    return PagoSocioDetalle(**pago_dict)


@router.get("/{socio_id}/estadisticas", response_model=PagoSocioEstadistico)
async def estadisticas_socio(
    socio_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Obtener estadísticas financieras de un socio"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado"
        )

    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)

    # Estadísticas generales
    total_aportes = db.query(func.sum(PagoSocio.monto)).filter(
        PagoSocio.socio_id == socio_id,
        PagoSocio.tipo == "aporte"
    ).scalar() or 0

    total_prestamos = db.query(func.sum(PagoSocio.monto)).filter(
        PagoSocio.socio_id == socio_id,
        PagoSocio.tipo == "prestamo"
    ).scalar() or 0

    total_devoluciones = db.query(func.sum(PagoSocio.monto)).filter(
        PagoSocio.socio_id == socio_id,
        PagoSocio.tipo == "devolucion"
    ).scalar() or 0

    total_ganancias = db.query(func.sum(PagoSocio.monto)).filter(
        PagoSocio.socio_id == socio_id,
        PagoSocio.tipo == "ganancia"
    ).scalar() or 0

    # Pagos del mes actual
    pagos_mes = db.query(func.count(PagoSocio.id)).filter(
        PagoSocio.socio_id == socio_id,
        func.date(PagoSocio.fecha_pago) >= inicio_mes
    ).scalar()

    monto_mes = db.query(func.sum(PagoSocio.monto)).filter(
        PagoSocio.socio_id == socio_id,
        func.date(PagoSocio.fecha_pago) >= inicio_mes
    ).scalar() or 0

    return PagoSocioEstadistico(
        socio_id=socio_id,
        socio_nombre=socio.nombre_completo,
        total_aportes=Decimal(str(float(total_aportes or 0))),
        total_prestamos=Decimal(str(float(total_prestamos or 0))),
        total_devoluciones=Decimal(str(float(total_devoluciones or 0))),
        total_ganancias=Decimal(str(float(total_ganancias or 0))),
        saldo_actual=socio.capital_actual,
        pagos_mes_actual=pagos_mes,
        monto_mes_actual=Decimal(str(float(monto_mes or 0)))
    )


# ========== ENDPOINTS HTML ==========

@router.get("/crear", response_class=HTMLResponse)
async def pagina_crear_socio(
    request: Request,
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Página para crear nuevo socio"""
    return templates.TemplateResponse(
        "socios/crear.html",
        {"request": request, "user": current_user}
    )


@router.get("/{socio_id}/editar", response_class=HTMLResponse)
async def pagina_editar_socio(
    socio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_admin_user)
):
    """Página para editar socio"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    return templates.TemplateResponse(
        "socios/editar.html",
        {"request": request, "user": current_user, "socio": socio}
    )


@router.get("/{socio_id}/detalle", response_class=HTMLResponse)
async def pagina_detalle_socio(
    socio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Página de detalle de socio"""
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    return templates.TemplateResponse(
        "socios/detalle.html",
        {"request": request, "user": current_user, "socio": socio}
    )


@router.get("/pagos", response_class=HTMLResponse)
async def pagina_pagos_socios(
    request: Request,
    current_user: UsuarioModel = Depends(get_current_user)
):
    """Página de pagos de socios"""
    return templates.TemplateResponse(
        "socios/pagos.html",
        {"request": request, "user": current_user}
    )
