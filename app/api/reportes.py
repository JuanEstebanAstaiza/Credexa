"""
Endpoints de gestión de reportes
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, extract
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import Usuario
from app.models.pago import Pago
from app.models.prestamo import Prestamo
from app.models.cliente import Cliente
from app.schemas.reporte import (
    ReportePago, ReporteMoroso, ReportePagoFiltro,
    ReporteMorosoFiltro, ReporteEstadistico
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Endpoints API REST

def _get_pagos_data(filtros: ReportePagoFiltro, db: Session, current_user: Usuario):
    """Función helper para obtener datos de pagos"""
    # Consulta base con joins
    query = db.query(
        Pago,
        Prestamo,
        Cliente
    ).join(
        Prestamo, Pago.prestamo_id == Prestamo.id
    ).join(
        Cliente, Prestamo.cliente_id == Cliente.id
    ).filter(
        Pago.fecha_pago >= filtros.fecha_desde,
        Pago.fecha_pago <= filtros.fecha_hasta
    )

    # Aplicar filtros opcionales
    if filtros.tipo_pago:
        query = query.filter(Pago.tipo_pago == filtros.tipo_pago)
    if filtros.metodo_pago:
        query = query.filter(Pago.metodo_pago == filtros.metodo_pago)
    if filtros.prestamo_id:
        query = query.filter(Pago.prestamo_id == filtros.prestamo_id)
    if filtros.cliente_id:
        query = query.filter(Cliente.id == filtros.cliente_id)
    if filtros.cliente_nombre and filtros.cliente_nombre.strip():
        query = query.filter(Cliente.nombre_completo.ilike(f"%{filtros.cliente_nombre}%"))
    if filtros.cliente_cedula and filtros.cliente_cedula.strip():
        query = query.filter(Cliente.cedula.ilike(f"%{filtros.cliente_cedula}%"))
    if filtros.monto_min:
        query = query.filter(Pago.monto_pagado >= filtros.monto_min)
    if filtros.monto_max:
        query = query.filter(Pago.monto_pagado <= filtros.monto_max)

    # Ordenar por fecha descendente
    query = query.order_by(Pago.fecha_pago.desc())

    resultados = query.all()

    # Convertir a formato de reporte
    reportes = []
    for pago, prestamo, cliente in resultados:
        reporte = ReportePago(
            id=pago.id,
            fecha_pago=pago.fecha_pago,
            monto_pagado=pago.monto_pagado,
            tipo_pago=pago.tipo_pago,
            metodo_pago=pago.metodo_pago,
            numero_cuota=pago.numero_cuota,
            capital_pagado=pago.capital_pagado,
            intereses_pagados=pago.intereses_pagados,
            referencia_pago=pago.referencia_pago,
            prestamo_id=prestamo.id,
            prestamo_monto=prestamo.monto,
            prestamo_estado=prestamo.estado,
            cliente_id=cliente.id,
            cliente_nombre=cliente.nombre_completo,
            cliente_cedula=cliente.cedula
        )
        reportes.append(reporte)

    return reportes

@router.post("/pagos", response_model=List[ReportePago])
async def reporte_pagos_fecha(
    filtros: ReportePagoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Generar reporte de pagos por rango de fechas"""
    return _get_pagos_data(filtros, db, current_user)

@router.post("/morosos", response_model=List[ReporteMoroso])
async def reporte_clientes_morosos(
    filtros: ReporteMorosoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Generar reporte de clientes morosos"""
    hoy = date.today()

    # Subconsulta para obtener la última fecha de pago de cada préstamo
    ultima_fecha_subquery = db.query(
        Pago.prestamo_id,
        func.max(Pago.fecha_pago).label('ultima_fecha_pago')
    ).group_by(Pago.prestamo_id).subquery()

    # Consulta principal de préstamos activos
    query = db.query(
        Prestamo,
        Cliente,
        ultima_fecha_subquery.c.ultima_fecha_pago
    ).join(
        Cliente, Prestamo.cliente_id == Cliente.id
    ).outerjoin(
        ultima_fecha_subquery,
        Prestamo.id == ultima_fecha_subquery.c.prestamo_id
    ).filter(
        Prestamo.estado == "activo"
    )

    resultados = query.all()

    morosos = []
    for prestamo, cliente, ultima_fecha_pago in resultados:
        # Calcular días de mora
        if ultima_fecha_pago:
            # Calcular próxima cuota (última fecha de pago + 1 mes)
            proxima_cuota = ultima_fecha_pago.date() + timedelta(days=30)
            if proxima_cuota < hoy:
                dias_mora = (hoy - proxima_cuota).days
            else:
                continue  # No está en mora
        else:
            # Si nunca ha pagado, calcular desde fecha de inicio + 30 días
            fecha_vencimiento = prestamo.fecha_inicio.date() + timedelta(days=30)
            if fecha_vencimiento < hoy:
                dias_mora = (hoy - fecha_vencimiento).days
            else:
                continue  # No está en mora

        # Calcular monto en mora (cuotas pendientes aproximadas)
        cuotas_pendientes = prestamo.numero_cuotas - prestamo.cuotas_pagadas
        if cuotas_pendientes > 0:
            monto_mora = (prestamo.valor_cuota * cuotas_pendientes)
        else:
            # Si no hay cuotas pendientes pero está en mora, usar saldo pendiente
            monto_mora = prestamo.saldo_pendiente

        # Aplicar filtros
        if filtros.cliente_id and cliente.id != filtros.cliente_id:
            continue
        if filtros.cliente_nombre and filtros.cliente_nombre.strip():
            if filtros.cliente_nombre.lower() not in cliente.nombre_completo.lower():
                continue
        if filtros.cliente_cedula and filtros.cliente_cedula.strip():
            if filtros.cliente_cedula not in cliente.cedula:
                continue
        if filtros.dias_mora_min and dias_mora < filtros.dias_mora_min:
            continue
        if filtros.monto_min and monto_mora < filtros.monto_min:
            continue

        reporte = ReporteMoroso(
            cliente_id=cliente.id,
            cliente_nombre=cliente.nombre_completo,
            cliente_cedula=cliente.cedula,
            cliente_telefono=cliente.telefono,
            prestamo_id=prestamo.id,
            prestamo_monto=prestamo.monto,
            prestamo_fecha_inicio=prestamo.fecha_inicio,
            saldo_pendiente=prestamo.saldo_pendiente,
            cuotas_pagadas=prestamo.cuotas_pagadas,
            cuotas_totales=prestamo.numero_cuotas,
            dias_mora=dias_mora,
            monto_mora=monto_mora,
            ultima_cuota_fecha=ultima_fecha_pago
        )
        morosos.append(reporte)

    # Ordenar por días de mora descendente
    morosos.sort(key=lambda x: x.dias_mora, reverse=True)

    return morosos

@router.get("/estadisticas", response_model=ReporteEstadistico)
async def estadisticas_generales(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener estadísticas generales del sistema"""
    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)
    inicio_dia = date(hoy.year, hoy.month, hoy.day)

    # Estadísticas de pagos
    pagos_total = db.query(func.count(Pago.id)).scalar()
    monto_total_pagos = db.query(func.sum(Pago.monto_pagado)).scalar() or 0

    pagos_dia = db.query(func.count(Pago.id)).filter(
        func.date(Pago.fecha_pago) == inicio_dia
    ).scalar()

    monto_dia = db.query(func.sum(Pago.monto_pagado)).filter(
        func.date(Pago.fecha_pago) == inicio_dia
    ).scalar() or 0

    pagos_mes = db.query(func.count(Pago.id)).filter(
        func.date(Pago.fecha_pago) >= inicio_mes
    ).scalar()

    monto_mes = db.query(func.sum(Pago.monto_pagado)).filter(
        func.date(Pago.fecha_pago) >= inicio_mes
    ).scalar() or 0

    # Estadísticas de préstamos
    prestamos_activos = db.query(func.count(Prestamo.id)).filter(
        Prestamo.estado == "activo"
    ).scalar()

    prestamos_pagados = db.query(func.count(Prestamo.id)).filter(
        Prestamo.estado == "pagado"
    ).scalar()

    # Calcular clientes morosos dinámicamente (misma lógica que endpoint de morosos)
    clientes_morosos = 0
    monto_mora_total = 0

    # Subconsulta para obtener la última fecha de pago de cada préstamo activo
    ultima_fecha_subquery = db.query(
        Pago.prestamo_id,
        func.max(Pago.fecha_pago).label('ultima_fecha_pago')
    ).group_by(Pago.prestamo_id).subquery()

    # Consulta de préstamos activos con su última fecha de pago
    prestamos_activos_query = db.query(
        Prestamo,
        ultima_fecha_subquery.c.ultima_fecha_pago
    ).join(
        ultima_fecha_subquery,
        Prestamo.id == ultima_fecha_subquery.c.prestamo_id,
        isouter=True
    ).filter(Prestamo.estado == "activo").all()

    for prestamo, ultima_fecha_pago in prestamos_activos_query:
        # Calcular días de mora y monto
        if ultima_fecha_pago:
            # Calcular próxima cuota (última fecha de pago + 1 mes)
            proxima_cuota = ultima_fecha_pago.date() + timedelta(days=30)
            if proxima_cuota < hoy:
                clientes_morosos += 1
                # Calcular monto en mora (cuotas pendientes aproximadas)
                cuotas_pendientes = prestamo.numero_cuotas - prestamo.cuotas_pagadas
                if cuotas_pendientes > 0:
                    monto_mora_total += float((prestamo.valor_cuota * cuotas_pendientes))
                else:
                    monto_mora_total += float(prestamo.saldo_pendiente)
        else:
            # Si nunca ha pagado, calcular desde fecha de inicio + 30 días
            fecha_vencimiento = prestamo.fecha_inicio.date() + timedelta(days=30)
            if fecha_vencimiento < hoy:
                clientes_morosos += 1
                monto_mora_total += float(prestamo.saldo_pendiente)

    return ReporteEstadistico(
        total_pagos=pagos_total,
        monto_total_pagos=monto_total_pagos,
        pagos_dia_actual=pagos_dia,
        monto_dia_actual=monto_dia,
        pagos_mes_actual=pagos_mes,
        monto_mes_actual=monto_mes,
        clientes_morosos=clientes_morosos,
        monto_mora_total=monto_mora_total,
        prestamos_activos=prestamos_activos,
        prestamos_pagados=prestamos_pagados
    )

# Endpoints para páginas HTML

@router.get("", response_class=HTMLResponse)
async def pagina_reportes(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página principal de reportes"""
    return templates.TemplateResponse("reportes/index.html", {
        "request": request,
        "title": "Reportes del Sistema",
        "user": current_user
    })

@router.get("/pagos", response_class=HTMLResponse)
async def pagina_reporte_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de reporte de pagos por fecha"""
    return templates.TemplateResponse("reportes/pagos.html", {
        "request": request,
        "title": "Reporte de Pagos",
        "user": current_user
    })

@router.get("/morosos", response_class=HTMLResponse)
async def pagina_reporte_morosos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de reporte de clientes morosos"""
    return templates.TemplateResponse("reportes/morosos.html", {
        "request": request,
        "title": "Clientes Morosos",
        "user": current_user
    })

# Endpoints de Exportación

@router.post("/export/pagos/excel")
async def exportar_pagos_excel(
    filtros: ReportePagoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de pagos a Excel"""
    # Obtener los datos del reporte
    pagos = _get_pagos_data(filtros, db, current_user)

    if not pagos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos para exportar"
        )

    # Crear DataFrame de pandas
    data = []
    for pago in pagos:
        data.append({
            'ID Pago': pago.id,
            'Fecha': pago.fecha_pago.strftime('%Y-%m-%d'),
            'Cliente': pago.cliente_nombre,
            'Cédula': pago.cliente_cedula,
            'Préstamo ID': pago.prestamo_id,
            'Monto Préstamo': pago.prestamo_monto,
            'Monto Pagado': pago.monto_pagado,
            'Tipo Pago': pago.tipo_pago,
            'Método Pago': pago.metodo_pago or '',
            'Capital Pagado': pago.capital_pagado,
            'Intereses Pagados': pago.intereses_pagados,
            'Referencia': pago.referencia_pago or ''
        })

    df = pd.DataFrame(data)

    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Pagos', index=False)

        # Dar formato al Excel
        worksheet = writer.sheets['Pagos']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    # Nombre del archivo con fecha
    fecha_inicio = filtros.fecha_desde.strftime('%Y%m%d')
    fecha_fin = filtros.fecha_hasta.strftime('%Y%m%d')
    filename = f"reporte_pagos_{fecha_inicio}_{fecha_fin}.xlsx"

    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/export/pagos/pdf")
async def exportar_pagos_pdf(
    filtros: ReportePagoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de pagos a PDF"""
    # Obtener los datos del reporte
    pagos = _get_pagos_data(filtros, db, current_user)

    if not pagos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos para exportar"
        )

    # Crear PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    titulo = Paragraph("Reporte de Pagos", styles['Heading1'])
    elements.append(titulo)
    elements.append(Spacer(1, 12))

    # Información del período
    periodo = Paragraph(
        f"Período: {filtros.fecha_desde.strftime('%d/%m/%Y')} - {filtros.fecha_hasta.strftime('%d/%m/%Y')}",
        styles['Normal']
    )
    elements.append(periodo)
    elements.append(Spacer(1, 12))

    # Datos de la tabla
    data = [['ID', 'Fecha', 'Cliente', 'Monto', 'Tipo', 'Método']]

    for pago in pagos:
        data.append([
            str(pago.id),
            pago.fecha_pago.strftime('%d/%m/%Y'),
            pago.cliente_nombre[:20] + '...' if len(pago.cliente_nombre) > 20 else pago.cliente_nombre,
            f"${pago.monto_pagado:,.0f}",
            pago.tipo_pago,
            pago.metodo_pago or ''
        ])

    # Crear tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # Resumen
    total_pagos = len(pagos)
    total_monto = sum(pago.monto_pagado for pago in pagos)

    elements.append(Spacer(1, 20))
    resumen = Paragraph(
        f"Total de pagos: {total_pagos} | Monto total: ${total_monto:,.0f}",
        styles['Heading3']
    )
    elements.append(resumen)

    doc.build(elements)
    buffer.seek(0)

    # Nombre del archivo
    fecha_inicio = filtros.fecha_desde.strftime('%Y%m%d')
    fecha_fin = filtros.fecha_hasta.strftime('%Y%m%d')
    filename = f"reporte_pagos_{fecha_inicio}_{fecha_fin}.pdf"

    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type='application/pdf',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/export/morosos/excel")
async def exportar_morosos_excel(
    filtros: ReporteMorosoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de clientes morosos a Excel"""
    # Obtener los datos del reporte
    morosos = await reporte_clientes_morosos(filtros, db, current_user)

    if not morosos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos para exportar"
        )

    # Crear DataFrame de pandas
    data = []
    for moroso in morosos:
        data.append({
            'Cliente': moroso.cliente_nombre,
            'Cédula': moroso.cliente_cedula,
            'Teléfono': moroso.cliente_telefono or '',
            'Préstamo ID': moroso.prestamo_id,
            'Monto Préstamo': moroso.prestamo_monto,
            'Saldo Pendiente': moroso.saldo_pendiente,
            'Cuotas Pagadas': f"{moroso.cuotas_pagadas}/{moroso.cuotas_totales}",
            'Días de Mora': moroso.dias_mora,
            'Monto en Mora': moroso.monto_mora,
            'Último Pago': moroso.ultima_cuota_fecha.strftime('%Y-%m-%d') if moroso.ultima_cuota_fecha else 'Nunca'
        })

    df = pd.DataFrame(data)

    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Clientes_Morosos', index=False)

        # Dar formato al Excel
        worksheet = writer.sheets['Clientes_Morosos']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    filename = f"reporte_clientes_morosos_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/export/pagos/csv")
async def exportar_pagos_csv(
    filtros: ReportePagoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de pagos a CSV"""
    # Obtener los datos del reporte
    pagos = _get_pagos_data(filtros, db, current_user)

    if not pagos:
        # Crear CSV vacío con headers
        csv_content = 'ID Pago,Fecha,Hora,Cliente,Cédula,Préstamo ID,Monto Préstamo,Monto Pagado,Capital Pagado,Intereses Pagados,Número Cuota,Tipo Pago,Método Pago,Referencia\n'
    else:
        # Crear contenido CSV
        headers = [
            'ID Pago',
            'Fecha',
            'Hora',
            'Cliente',
            'Cédula',
            'Préstamo ID',
            'Monto Préstamo',
            'Monto Pagado',
            'Capital Pagado',
            'Intereses Pagados',
            'Número Cuota',
            'Tipo Pago',
            'Método Pago',
            'Referencia'
        ]

        csv_lines = [headers.join(',')]
        for pago in pagos:
            try:
                # Asegurar que fecha_pago sea datetime
                fecha = pago.fecha_pago
                if hasattr(fecha, 'date'):  # Si es datetime
                    fecha_str = fecha.strftime('%d/%m/%Y')
                    hora_str = fecha.strftime('%H:%M')
                else:  # Si ya es string
                    fecha_str = str(fecha)[:10]  # YYYY-MM-DD
                    hora_str = '00:00'

                line = ','.join([
                    str(pago.id or ''),
                    fecha_str,
                    hora_str,
                    f'"{pago.cliente_nombre or ""}"',
                    str(pago.cliente_cedula or ''),
                    str(pago.prestamo_id or ''),
                    str(pago.prestamo_monto or ''),
                    str(pago.monto_pagado or ''),
                    str(pago.capital_pagado or ''),
                    str(pago.intereses_pagados or ''),
                    str(pago.numero_cuota or ''),
                    str(pago.tipo_pago or ''),
                    str(pago.metodo_pago or ''),
                    f'"{pago.referencia_pago or ""}"'
                ])
                csv_lines.append(line)
            except Exception as e:
                # Si hay error con un pago, agregar una línea de error
                csv_lines.append(f'ERROR procesando pago {pago.id}: {str(e)}')

        csv_content = '\n'.join(csv_lines)

    # Crear y devolver archivo CSV
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename=reporte_pagos_{filtros.fecha_desde.strftime('%Y%m%d')}_{filtros.fecha_hasta.strftime('%Y%m%d')}.csv"}
    )

@router.post("/export/morosos/excel")
async def exportar_morosos_excel(
    filtros: ReporteMorosoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de clientes morosos a Excel"""
    morosos = await reporte_clientes_morosos(filtros, db, current_user)
    if not morosos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay datos para exportar")

    data = []
    for moroso in morosos:
        data.append({
            'Cliente': moroso.cliente_nombre,
            'Cédula': moroso.cliente_cedula,
            'Teléfono': moroso.cliente_telefono or '',
            'Préstamo ID': moroso.prestamo_id,
            'Monto Préstamo': moroso.prestamo_monto,
            'Saldo Pendiente': moroso.saldo_pendiente,
            'Cuotas Pagadas': moroso.cuotas_pagadas,
            'Total Cuotas': moroso.cuotas_totales,
            'Días de Mora': moroso.dias_mora,
            'Monto en Mora': moroso.monto_mora,
            'Último Pago': moroso.ultima_cuota_fecha.strftime('%Y-%m-%d') if moroso.ultima_cuota_fecha else 'Nunca'
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Morosos', index=False)
        worksheet = writer.sheets['Morosos']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    fecha_actual = datetime.now().strftime('%Y%m%d')
    filename = f"reporte_clientes_morosos_{fecha_actual}.xlsx"
    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/export/morosos/csv")
async def exportar_morosos_csv(
    filtros: ReporteMorosoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de clientes morosos a CSV"""
    # Obtener los datos del reporte
    morosos = await reporte_clientes_morosos(filtros, db, current_user)

    if not morosos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos para exportar"
        )

    # Crear contenido CSV
    headers = [
        'Cliente',
        'Cédula',
        'Teléfono',
        'Préstamo ID',
        'Monto Préstamo',
        'Saldo Pendiente',
        'Cuotas Pagadas',
        'Total Cuotas',
        'Días de Mora',
        'Monto en Mora',
        'Último Pago'
    ]

    csv_lines = [headers.join(',')]
    for moroso in morosos:
        line = ','.join([
            f'"{moroso.cliente_nombre}"',
            str(moroso.cliente_cedula),
            str(moroso.cliente_telefono or ''),
            str(moroso.prestamo_id),
            str(moroso.prestamo_monto),
            str(moroso.saldo_pendiente),
            str(moroso.cuotas_pagadas),
            str(moroso.cuotas_totales),
            str(moroso.dias_mora),
            str(moroso.monto_mora),
            moroso.ultima_cuota_fecha.strftime('%Y-%m-%d') if moroso.ultima_cuota_fecha else 'Nunca'
        ])
        csv_lines.append(line)

    csv_content = '\n'.join(csv_lines)

    # Crear y devolver archivo CSV
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename=reporte_clientes_morosos_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.post("/export/morosos/pdf")
async def exportar_morosos_pdf(
    filtros: ReporteMorosoFiltro,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exportar reporte de clientes morosos a PDF"""
    # Obtener los datos del reporte
    morosos = await reporte_clientes_morosos(filtros, db, current_user)

    if not morosos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos para exportar"
        )

    # Crear PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    titulo = Paragraph("Reporte de Clientes Morosos", styles['Heading1'])
    elements.append(titulo)
    elements.append(Spacer(1, 12))

    # Información del reporte
    fecha = Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.append(fecha)
    elements.append(Spacer(1, 12))

    # Datos de la tabla
    data = [['Cliente', 'Cédula', 'Días Mora', 'Monto Mora', 'Teléfono']]

    for moroso in morosos:
        data.append([
            moroso.cliente_nombre[:25] + '...' if len(moroso.cliente_nombre) > 25 else moroso.cliente_nombre,
            moroso.cliente_cedula,
            str(moroso.dias_mora),
            f"${moroso.monto_mora:,.0f}",
            moroso.cliente_telefono or ''
        ])

    # Crear tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # Resumen
    total_morosos = len(morosos)
    total_monto = sum(moroso.monto_mora for moroso in morosos)

    elements.append(Spacer(1, 20))
    resumen = Paragraph(
        f"Total de clientes morosos: {total_morosos} | Monto total en mora: ${total_monto:,.0f}",
        styles['Heading3']
    )
    elements.append(resumen)

    doc.build(elements)
    buffer.seek(0)

    filename = f"reporte_clientes_morosos_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type='application/pdf',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Endpoints para Gráficas

@router.get("/charts/prestamos-estado")
async def chart_prestamos_estado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Datos para gráfica de distribución de préstamos por estado"""
    hoy = date.today()

    # Contar préstamos pagados
    prestamos_pagados = db.query(func.count(Prestamo.id)).filter(
        Prestamo.estado == "pagado"
    ).scalar()

    # Calcular préstamos activos al día y en mora
    prestamos_al_dia = 0
    prestamos_en_mora = 0

    # Subconsulta para obtener la última fecha de pago de cada préstamo activo
    ultima_fecha_subquery = db.query(
        Pago.prestamo_id,
        func.max(Pago.fecha_pago).label('ultima_fecha_pago')
    ).group_by(Pago.prestamo_id).subquery()

    # Consulta de préstamos activos con su última fecha de pago
    prestamos_activos_query = db.query(
        Prestamo,
        ultima_fecha_subquery.c.ultima_fecha_pago
    ).join(
        ultima_fecha_subquery,
        Prestamo.id == ultima_fecha_subquery.c.prestamo_id,
        isouter=True
    ).filter(Prestamo.estado == "activo").all()

    for prestamo, ultima_fecha_pago in prestamos_activos_query:
        # Calcular si está en mora
        if ultima_fecha_pago:
            # Calcular próxima cuota (última fecha de pago + 1 mes)
            proxima_cuota = ultima_fecha_pago.date() + timedelta(days=30)
            if proxima_cuota < hoy:
                prestamos_en_mora += 1
            else:
                prestamos_al_dia += 1
        else:
            # Si nunca ha pagado, calcular desde fecha de inicio + 30 días
            fecha_vencimiento = prestamo.fecha_inicio.date() + timedelta(days=30)
            if fecha_vencimiento < hoy:
                prestamos_en_mora += 1
            else:
                prestamos_al_dia += 1

    return {
        "labels": ["Al Día", "En Mora", "Pagados"],
        "data": [prestamos_al_dia, prestamos_en_mora, prestamos_pagados],
        "colors": ["#28a745", "#dc3545", "#6c757d"]
    }

@router.get("/charts/pagos-metodo")
async def chart_pagos_metodo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Datos para gráfica de pagos por método"""
    # Consulta de pagos agrupados por método
    resultados = db.query(
        Pago.metodo_pago,
        func.count(Pago.id).label('cantidad'),
        func.sum(Pago.monto_pagado).label('total')
    ).group_by(Pago.metodo_pago).all()

    labels = []
    data = []
    colors = {
        'efectivo': '#28a745',
        'transferencia': '#007bff',
        'cheque': '#ffc107',
        'tarjeta': '#17a2b8'
    }

    for metodo, cantidad, total in resultados:
        metodo_label = metodo or 'No especificado'
        labels.append(f"{metodo_label} ({cantidad})")
        data.append(float(total))

    return {
        "labels": labels,
        "data": data,
        "colors": [colors.get(metodo, '#6c757d') for metodo, _, _ in resultados]
    }

@router.get("/charts/evolucion-pagos")
async def chart_evolucion_pagos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Datos para gráfica de evolución de pagos (últimos 6 meses)"""
    # Generar últimos 6 meses
    hoy = date.today()
    labels = []
    data = []

    for i in range(5, -1, -1):  # 6 meses hacia atrás
        # Calcular fecha de inicio del mes
        year = hoy.year
        month = hoy.month - i
        if month <= 0:
            year -= 1
            month += 12

        fecha_inicio = date(year, month, 1)

        # Calcular fecha de fin del mes
        if month == 12:
            fecha_fin = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            fecha_fin = date(year, month + 1, 1) - timedelta(days=1)

        # Si es el mes actual, usar fecha actual
        if i == 0:
            fecha_fin = hoy

        # Obtener total de pagos para este mes
        total_mes = db.query(func.sum(Pago.monto_pagado)).filter(
            func.date(Pago.fecha_pago) >= fecha_inicio,
            func.date(Pago.fecha_pago) <= fecha_fin
        ).scalar() or 0

        # Formatear etiqueta del mes
        mes_nombre = fecha_inicio.strftime('%b %Y')
        labels.append(mes_nombre)
        data.append(float(total_mes))

    return {
        "labels": labels,
        "data": data
    }

@router.get("/charts/tipos-pago")
async def chart_tipos_pago(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Datos para gráfica de tipos de pago"""
    # Consulta de pagos agrupados por tipo
    resultados = db.query(
        Pago.tipo_pago,
        func.count(Pago.id).label('cantidad'),
        func.sum(Pago.monto_pagado).label('total')
    ).group_by(Pago.tipo_pago).all()

    labels = []
    data = []
    colors = {
        'cuota': '#28a745',
        'abono': '#ffc107',
        'refinanciacion': '#dc3545'
    }

    for tipo, cantidad, total in resultados:
        tipo_label = tipo or 'No especificado'
        labels.append(f"{tipo_label} ({cantidad})")
        data.append(float(total))

    return {
        "labels": labels,
        "data": data,
        "colors": [colors.get(tipo, '#6c757d') for tipo, _, _ in resultados]
    }
