"""
Endpoints de gestión de clientes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import Usuario
from app.models.cliente import Cliente
from app.schemas.cliente import (
    Cliente as ClienteSchema, ClienteCreate, ClienteUpdate,
    ClienteFiltro, ClientePaginado
)

router = APIRouter()

# Endpoints API REST

@router.post("", response_model=ClienteSchema)
async def crear_cliente(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo cliente"""
    # Verificar si la cédula ya existe
    existing_cliente = db.query(Cliente).filter(Cliente.cedula == cliente_data.cedula).first()
    if existing_cliente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con esta cédula",
        )

    # Crear nuevo cliente
    db_cliente = Cliente(**cliente_data.dict())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)

    return db_cliente

@router.get("", response_model=ClientePaginado)
async def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    nombre: Optional[str] = None,
    cedula: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    activo: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar clientes con filtros y paginación"""
    # Construir filtros
    filtros = []
    if nombre:
        filtros.append(Cliente.nombre_completo.ilike(f"%{nombre}%"))
    if cedula:
        filtros.append(Cliente.cedula.ilike(f"%{cedula}%"))
    if telefono:
        filtros.append(Cliente.telefono.ilike(f"%{telefono}%"))
    if email:
        filtros.append(Cliente.email.ilike(f"%{email}%"))
    if activo is not None:
        filtros.append(Cliente.activo == activo)

    # Consulta base
    query = db.query(Cliente)

    # Aplicar filtros
    if filtros:
        query = query.filter(and_(*filtros))

    # Obtener total
    total = query.count()

    # Aplicar paginación y ordenar
    clientes = query.order_by(Cliente.nombre_completo).offset(skip).limit(limit).all()

    # Calcular páginas
    paginas_totales = (total + limit - 1) // limit if total > 0 else 1
    pagina_actual = (skip // limit) + 1

    return ClientePaginado(
        items=clientes,
        total=total,
        pagina=pagina_actual,
        por_pagina=limit,
        paginas_totales=paginas_totales
    )

@router.get("/{cliente_id}", response_model=ClienteSchema)
async def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un cliente por ID"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )
    return cliente

@router.put("/{cliente_id}", response_model=ClienteSchema)
async def actualizar_cliente(
    cliente_id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un cliente"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )

    # Verificar cédula única si se está cambiando
    if cliente_data.cedula and cliente_data.cedula != cliente.cedula:
        existing_cliente = db.query(Cliente).filter(Cliente.cedula == cliente_data.cedula).first()
        if existing_cliente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con esta cédula",
            )

    # Actualizar campos
    update_data = cliente_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cliente, field, value)

    db.commit()
    db.refresh(cliente)

    return cliente

@router.delete("/{cliente_id}")
async def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un cliente (desactivar)"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )

    # Desactivar cliente en lugar de eliminar
    cliente.activo = 0
    db.commit()

    return {"message": "Cliente desactivado exitosamente"}

@router.post("/{cliente_id}/activar")
async def activar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reactivar un cliente"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )

    cliente.activo = 1
    db.commit()

    return {"message": "Cliente activado exitosamente"}

# Las rutas HTML están definidas en main.py
