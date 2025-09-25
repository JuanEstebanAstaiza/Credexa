"""
Endpoints de gestión de préstamos
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import Usuario
from app.models.cliente import Cliente
from app.models.prestamo import Prestamo
from app.models.pago import Pago
from app.schemas.prestamo import (
    Prestamo as PrestamoSchema, PrestamoCreate, PrestamoUpdate,
    PrestamoFiltro, PrestamoPaginado, EstadisticasPrestamo,
    RefinanciacionCreate
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Endpoints API REST

@router.post("", response_model=PrestamoSchema)
async def crear_prestamo(
    prestamo_data: PrestamoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo préstamo"""
    # Verificar que el cliente existe y está activo
    cliente = db.query(Cliente).filter(Cliente.id == prestamo_data.cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )

    if not cliente.is_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden crear préstamos para clientes inactivos",
        )

    # Verificar que no existe un préstamo activo para este cliente (opcional)
    prestamo_activo = db.query(Prestamo).filter(
        and_(
            Prestamo.cliente_id == prestamo_data.cliente_id,
            Prestamo.estado == "activo"
        )
    ).first()

    if prestamo_activo and not prestamo_data.es_refinanciacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente ya tiene un préstamo activo",
        )

    # Crear el préstamo
    db_prestamo = Prestamo(**prestamo_data.dict())

    # Calcular valores automáticos
    db_prestamo.numero_cuotas = db_prestamo.plazo_meses
    db_prestamo.valor_cuota = db_prestamo.calcular_cuota()

    # Calcular totales
    db_prestamo.total_intereses = (db_prestamo.valor_cuota * db_prestamo.numero_cuotas) - float(db_prestamo.monto)
    db_prestamo.total_pagar = db_prestamo.valor_cuota * db_prestamo.numero_cuotas
    db_prestamo.saldo_pendiente = db_prestamo.total_pagar

    # Redondear valores
    db_prestamo.total_intereses = round(db_prestamo.total_intereses, 2)
    db_prestamo.total_pagar = round(db_prestamo.total_pagar, 2)
    db_prestamo.saldo_pendiente = db_prestamo.total_pagar

    db.add(db_prestamo)
    db.commit()
    db.refresh(db_prestamo)

    return PrestamoSchema.from_orm_with_calculations(db_prestamo)

@router.get("", response_model=PrestamoPaginado)
async def listar_prestamos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    cliente_id: Optional[int] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    monto_min: Optional[Decimal] = None,
    monto_max: Optional[Decimal] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar préstamos con filtros y paginación"""
    # Construir filtros
    filtros = []

    if cliente_id:
        filtros.append(Prestamo.cliente_id == cliente_id)
    if estado:
        filtros.append(Prestamo.estado == estado)
    if fecha_desde:
        filtros.append(Prestamo.fecha_inicio >= fecha_desde)
    if fecha_hasta:
        filtros.append(Prestamo.fecha_inicio <= fecha_hasta)
    if monto_min:
        filtros.append(Prestamo.monto >= monto_min)
    if monto_max:
        filtros.append(Prestamo.monto <= monto_max)

    # Consulta base con joinedload para incluir información del cliente
    query = db.query(Prestamo).options(joinedload(Prestamo.cliente))

    # Aplicar filtros
    if filtros:
        query = query.filter(and_(*filtros))

    # Obtener total
    total = query.count()

    # Aplicar paginación y ordenar
    prestamos = query.order_by(Prestamo.fecha_inicio.desc()).offset(skip).limit(limit).all()

    # Convertir préstamos al esquema con cálculos automáticos
    prestamos_con_calculos = [
        PrestamoSchema.from_orm_with_calculations(prestamo)
        for prestamo in prestamos
    ]

    # Calcular páginas
    paginas_totales = (total + limit - 1) // limit if total > 0 else 1
    pagina_actual = (skip // limit) + 1

    return PrestamoPaginado(
        items=prestamos_con_calculos,
        total=total,
        pagina=pagina_actual,
        por_pagina=limit,
        paginas_totales=paginas_totales
    )

@router.get("/{prestamo_id}", response_model=PrestamoSchema)
async def obtener_prestamo(
    prestamo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un préstamo por ID"""
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    return PrestamoSchema.from_orm_with_calculations(prestamo)

@router.put("/{prestamo_id}", response_model=PrestamoSchema)
async def actualizar_prestamo(
    prestamo_id: int,
    prestamo_data: PrestamoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un préstamo (solo campos permitidos)"""
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    # Solo permitir actualizar campos que no afecten cálculos financieros
    campos_permitidos = ["observaciones"]

    # Aplicar solo campos permitidos
    update_data = {}
    for campo in campos_permitidos:
        if hasattr(prestamo_data, campo) and getattr(prestamo_data, campo) is not None:
            update_data[campo] = getattr(prestamo_data, campo)

    if update_data:
        for field, value in update_data.items():
            setattr(prestamo, field, value)

        db.commit()
        db.refresh(prestamo)

    return PrestamoSchema.from_orm_with_calculations(prestamo)

@router.delete("/{prestamo_id}")
async def eliminar_prestamo(
    prestamo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un préstamo (solo si no tiene pagos)"""
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    # Verificar si tiene pagos
    pagos_count = db.query(Pago).filter(Pago.prestamo_id == prestamo_id).count()
    if pagos_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un préstamo que tiene pagos registrados",
        )

    db.delete(prestamo)
    db.commit()

    return {"message": "Préstamo eliminado exitosamente"}

@router.get("/estadisticas/general", response_model=EstadisticasPrestamo)
async def obtener_estadisticas_prestamos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener estadísticas generales de préstamos"""
    # Consultas de agregación
    stats = db.query(
        func.count(Prestamo.id).label('total_prestamos'),
        func.sum(Prestamo.monto).label('monto_total_prestado'),
        func.sum(Prestamo.saldo_pendiente).label('monto_total_pendiente'),
        func.avg(Prestamo.tasa_interes).label('promedio_tasa_interes')
    ).first()

    # Contar por estado
    estados = db.query(
        Prestamo.estado,
        func.count(Prestamo.id).label('count')
    ).group_by(Prestamo.estado).all()

    # Convertir a diccionario
    estados_dict = {estado: count for estado, count in estados}

    # Calcular préstamos en mora dinámicamente usando la misma lógica que reportes/morosos
    hoy = date.today()
    prestamos_en_mora = 0

    # Para cada préstamo activo, verificar si está en mora
    prestamos_activos = db.query(Prestamo).filter(Prestamo.estado == "activo").all()

    for prestamo in prestamos_activos:
        # Obtener última fecha de pago para este préstamo
        ultima_fecha_pago = db.query(func.max(Pago.fecha_pago)).filter(
            Pago.prestamo_id == prestamo.id
        ).scalar()

        # Calcular días de mora
        if ultima_fecha_pago:
            # Calcular próxima cuota (última fecha de pago + 1 mes)
            proxima_cuota = ultima_fecha_pago.date() + timedelta(days=30)
            if proxima_cuota < hoy:
                prestamos_en_mora += 1
        else:
            # Si nunca ha pagado, calcular desde fecha de inicio + 30 días
            fecha_vencimiento = prestamo.fecha_inicio.date() + timedelta(days=30)
            if fecha_vencimiento < hoy:
                prestamos_en_mora += 1

    # Calcular monto total pagado
    monto_pagado = float(stats.monto_total_prestado or 0) - float(stats.monto_total_pendiente or 0)

    return EstadisticasPrestamo(
        total_prestamos=stats.total_prestamos or 0,
        prestamos_activos=estados_dict.get('activo', 0),
        prestamos_pagados=estados_dict.get('pagado', 0),
        prestamos_en_mora=prestamos_en_mora,
        monto_total_prestado=stats.monto_total_prestado or Decimal('0'),
        monto_total_pendiente=stats.monto_total_pendiente or Decimal('0'),
        monto_total_pagado=Decimal(str(monto_pagado)),
        promedio_tasa_interes=float(stats.promedio_tasa_interes or 0)
    )

@router.post("/prestamos/{prestamo_id}/refinanciar")
async def refinanciar_prestamo(
    prestamo_id: int,
    refinanciacion_data: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear una refinanciación de préstamo específico"""
    # Obtener préstamo original
    prestamo_original = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()

    if not prestamo_original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    if prestamo_original.estado not in ["activo", "mora"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden refinanciar préstamos activos o en mora",
        )

    if prestamo_original.saldo_pendiente <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El préstamo no tiene saldo pendiente para refinanciar",
        )

    # Validar datos de entrada
    nuevo_monto = refinanciacion_data.get("nuevo_monto", prestamo_original.saldo_pendiente)
    nueva_tasa = refinanciacion_data.get("nueva_tasa", prestamo_original.tasa_interes)
    nuevo_plazo = refinanciacion_data.get("nuevo_plazo", prestamo_original.numero_cuotas - prestamo_original.cuotas_pagadas)
    fecha_inicio_str = refinanciacion_data.get("fecha_inicio")
    observaciones = refinanciacion_data.get("observaciones", "Refinanciación del crédito")

    # Convertir fecha
    try:
        fecha_inicio = datetime.fromisoformat(fecha_inicio_str) if fecha_inicio_str else datetime.now()
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido",
        )

    # Validar rangos
    if nuevo_monto < 100000 or nuevo_monto > 50000000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto debe estar entre $100,000 y $50,000,000",
        )

    if nueva_tasa < 0.5 or nueva_tasa > 5.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La tasa debe estar entre 0.5% y 5.0%",
        )

    if nuevo_plazo < 1 or nuevo_plazo > 120:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El plazo debe estar entre 1 y 120 meses",
        )

    # Cambiar estado del préstamo original
    prestamo_original.estado = "refinanciado"
    prestamo_original.saldo_pendiente = Decimal('0')

    # Crear nuevo préstamo de refinanciación
    nuevo_prestamo = Prestamo(
        cliente_id=prestamo_original.cliente_id,
        monto=nuevo_monto,
        tasa_interes=nueva_tasa,
        plazo_meses=nuevo_plazo,
        fecha_inicio=fecha_inicio,
        observaciones=f"{observaciones} - Refinanciación de crédito #{prestamo_original.id}"
    )

    # Calcular valores automáticos
    nuevo_prestamo.numero_cuotas = nuevo_prestamo.plazo_meses
    nuevo_prestamo.valor_cuota = nuevo_prestamo.calcular_cuota()
    nuevo_prestamo.total_intereses = (nuevo_prestamo.valor_cuota * nuevo_prestamo.numero_cuotas) - float(nuevo_prestamo.monto)
    nuevo_prestamo.total_pagar = nuevo_prestamo.valor_cuota * nuevo_prestamo.numero_cuotas
    nuevo_prestamo.saldo_pendiente = nuevo_prestamo.total_pagar

    # Redondear valores
    nuevo_prestamo.total_intereses = round(nuevo_prestamo.total_intereses, 2)
    nuevo_prestamo.total_pagar = round(nuevo_prestamo.total_pagar, 2)

    db.add(nuevo_prestamo)
    db.commit()
    db.refresh(nuevo_prestamo)

    return {
        "message": "Refinanciación creada exitosamente",
        "nuevo_prestamo_id": nuevo_prestamo.id,
        "prestamo_original_id": prestamo_original.id,
        "monto_refinanciado": nuevo_monto,
        "nueva_cuota": float(nuevo_prestamo.valor_cuota)
    }

# Endpoints para páginas HTML

@router.get("/lista", response_class=HTMLResponse)
async def pagina_lista_prestamos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de listado de préstamos"""
    return templates.TemplateResponse("prestamos/lista.html", {
        "request": request,
        "title": "Lista de Créditos",
        "user": current_user
    })

@router.get("/nuevo", response_class=HTMLResponse)
async def pagina_nuevo_prestamo(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de creación de préstamo"""
    # Obtener lista de clientes activos para el select
    clientes = db.query(Cliente).filter(Cliente.activo == 1).order_by(Cliente.nombre_completo).all()

    return templates.TemplateResponse("prestamos/formulario.html", {
        "request": request,
        "title": "Nuevo Préstamo",
        "user": current_user,
        "modo": "crear",
        "clientes": clientes
    })

@router.get("/{prestamo_id}/detalle", response_class=HTMLResponse)
async def pagina_detalle_prestamo(
    prestamo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de detalle de préstamo"""
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    # Las propiedades calculadas se manejan en el esquema Pydantic

    return templates.TemplateResponse("prestamos/detalle.html", {
        "request": request,
        "title": f"Préstamo #{prestamo.id}",
        "user": current_user,
        "prestamo": prestamo
    })
