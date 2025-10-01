import os
import shutil
import mimetypes
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.core.security import get_current_admin_user, get_current_user
from app.models.user import Usuario
from app.models.carpeta import Carpeta
from app.models.documento import Documento
from app.schemas.carpeta import CarpetaCreate, CarpetaUpdate, CarpetaResponse, CarpetaTreeResponse
from app.schemas.documento import DocumentoCreate, DocumentoUpdate, DocumentoResponse
from app.services.documentos_service import DocumentosService

router = APIRouter()

# Directorio base para documentos
DOCUMENTOS_DIR = Path("documentos")
DOCUMENTOS_DIR.mkdir(exist_ok=True)

@router.get("/carpetas/arbol", response_model=CarpetaTreeResponse)
async def obtener_arbol_carpetas(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el árbol completo de carpetas"""
    def build_tree(carpeta):
        return CarpetaTreeResponse(
            id=carpeta.id,
            nombre=carpeta.nombre,
            ruta_completa=carpeta.ruta_completa,
            tipo=carpeta.tipo,
            subcarpetas=[build_tree(sub) for sub in carpeta.subcarpetas],
            documentos_count=len(carpeta.documentos)
        )

    # Obtener carpetas raíz (sin padre)
    carpetas_raiz = db.query(Carpeta).filter(Carpeta.parent_id.is_(None)).all()

    # Para simplificar, devolver una estructura con todas las carpetas raíz
    return CarpetaTreeResponse(
        id=0,
        nombre="Raíz",
        ruta_completa="",
        tipo="root",
        subcarpetas=[build_tree(c) for c in carpetas_raiz]
    )

@router.get("/carpetas", response_model=List[CarpetaResponse])
async def listar_carpetas(
    parent_id: Optional[int] = Query(None, description="ID de la carpeta padre"),
    tipo: Optional[str] = Query(None, description="Tipo de carpeta"),
    entidad_id: Optional[int] = Query(None, description="ID de la entidad"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar carpetas con filtros opcionales"""
    query = db.query(Carpeta)

    if parent_id is not None:
        query = query.filter(Carpeta.parent_id == parent_id)
    if tipo:
        query = query.filter(Carpeta.tipo == tipo)
    if entidad_id:
        query = query.filter(Carpeta.entidad_id == entidad_id)

    carpetas = query.all()

    # Convertir a response incluyendo conteos
    result = []
    for carpeta in carpetas:
        carpeta_dict = carpeta.__dict__.copy()
        carpeta_dict['documentos_count'] = len(carpeta.documentos)
        carpeta_dict['subcarpetas'] = [c.__dict__.copy() for c in carpeta.subcarpetas]
        for sub in carpeta_dict['subcarpetas']:
            sub['documentos_count'] = len(db.query(Documento).filter(Documento.carpeta_id == sub['id']).all())
        result.append(CarpetaResponse(**carpeta_dict))

    return result

@router.post("/carpetas", response_model=CarpetaResponse)
async def crear_carpeta(
    carpeta: CarpetaCreate,
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva carpeta"""
    # Validar que el parent existe si se especifica
    if carpeta.parent_id:
        parent = db.query(Carpeta).filter(Carpeta.id == carpeta.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Carpeta padre no encontrada")

    # Construir ruta completa
    ruta_completa = carpeta.nombre
    if carpeta.parent_id:
        parent = db.query(Carpeta).filter(Carpeta.id == carpeta.parent_id).first()
        ruta_completa = f"{parent.ruta_completa}/{carpeta.nombre}"

    # Crear directorio físico si no existe
    dir_path = DOCUMENTOS_DIR / ruta_completa
    dir_path.mkdir(parents=True, exist_ok=True)

    # Crear carpeta en BD
    db_carpeta = Carpeta(
        **carpeta.model_dump(),
        ruta_completa=ruta_completa,
        creada_por=current_user.id
    )

    db.add(db_carpeta)
    db.commit()
    db.refresh(db_carpeta)

    return CarpetaResponse(
        **db_carpeta.__dict__,
        documentos_count=0,
        subcarpetas=[]
    )

@router.get("/carpetas/{carpeta_id}", response_model=CarpetaResponse)
async def obtener_carpeta(
    carpeta_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener detalles de una carpeta específica"""
    carpeta = db.query(Carpeta).filter(Carpeta.id == carpeta_id).first()
    if not carpeta:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    return CarpetaResponse(
        **carpeta.__dict__,
        documentos_count=len(carpeta.documentos),
        subcarpetas=[c.__dict__.copy() for c in carpeta.subcarpetas]
    )

@router.put("/carpetas/{carpeta_id}", response_model=CarpetaResponse)
async def actualizar_carpeta(
    carpeta_id: int,
    carpeta_update: CarpetaUpdate,
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Actualizar una carpeta"""
    carpeta = db.query(Carpeta).filter(Carpeta.id == carpeta_id).first()
    if not carpeta:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    # Solo permitir actualizar carpetas no automáticas
    if carpeta.es_automatica:
        raise HTTPException(status_code=400, detail="No se pueden modificar carpetas automáticas")

    # Actualizar campos
    for field, value in carpeta_update.model_dump(exclude_unset=True).items():
        setattr(carpeta, field, value)

    # Si cambió el nombre, reconstruir ruta completa
    if carpeta_update.nombre and carpeta_update.nombre != carpeta.nombre:
        # Reconstruir rutas para esta carpeta y todas sus subcarpetas
        await _reconstruir_rutas(carpeta, db)

    db.commit()
    db.refresh(carpeta)

    return CarpetaResponse(
        **carpeta.__dict__,
        documentos_count=len(carpeta.documentos),
        subcarpetas=[c.__dict__.copy() for c in carpeta.subcarpetas]
    )

@router.delete("/carpetas/{carpeta_id}")
async def eliminar_carpeta(
    carpeta_id: int,
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Eliminar una carpeta y todo su contenido"""
    carpeta = db.query(Carpeta).filter(Carpeta.id == carpeta_id).first()
    if not carpeta:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    # No permitir eliminar carpetas automáticas
    if carpeta.es_automatica:
        raise HTTPException(status_code=400, detail="No se pueden eliminar carpetas automáticas")

    # Verificar que no tenga subcarpetas o documentos
    if carpeta.subcarpetas or carpeta.documentos:
        raise HTTPException(status_code=400, detail="La carpeta no está vacía")

    # Eliminar directorio físico
    dir_path = DOCUMENTOS_DIR / carpeta.ruta_completa
    if dir_path.exists():
        shutil.rmtree(dir_path)

    # Eliminar de BD
    db.delete(carpeta)
    db.commit()

    return {"message": "Carpeta eliminada exitosamente"}

# ===== DOCUMENTOS =====

@router.get("/documentos", response_model=List[DocumentoResponse])
async def listar_documentos(
    carpeta_id: Optional[int] = Query(None, description="ID de la carpeta"),
    tipo_documento: Optional[str] = Query(None, description="Tipo de documento"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar documentos con filtros opcionales"""
    query = db.query(Documento)

    if carpeta_id:
        query = query.filter(Documento.carpeta_id == carpeta_id)
    if tipo_documento:
        query = query.filter(Documento.tipo_documento == tipo_documento)

    documentos = query.all()
    return [DocumentoResponse.from_orm(doc) for doc in documentos]

@router.post("/documentos", response_model=DocumentoResponse)
async def subir_documento(
    background_tasks: BackgroundTasks,
    archivo: UploadFile = File(...),
    carpeta_id: int = Form(..., description="ID de la carpeta destino"),
    descripcion: Optional[str] = Form(None, description="Descripción del documento"),
    tipo_documento: Optional[str] = Form(None, description="Tipo de documento"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subir un nuevo documento"""
    # Verificar que la carpeta existe
    carpeta = db.query(Carpeta).filter(Carpeta.id == carpeta_id).first()
    if not carpeta:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    # Validar tamaño del archivo (máximo 10MB)
    if archivo.size and archivo.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande (máximo 10MB)")

    # Generar nombre único para el archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = Path(archivo.filename).suffix
    nombre_archivo = f"{timestamp}_{archivo.filename}"

    # Ruta completa del archivo
    ruta_archivo = f"{carpeta.ruta_completa}/{nombre_archivo}"

    # Crear documento en BD primero
    db_documento = Documento(
        nombre_original=archivo.filename,
        nombre_archivo=nombre_archivo,
        ruta_archivo=ruta_archivo,
        tipo_mime=archivo.content_type or mimetypes.guess_type(archivo.filename)[0],
        tamano=archivo.size or 0,
        carpeta_id=carpeta_id,
        usuario_subio_id=current_user.id,
        descripcion=descripcion,
        tipo_documento=tipo_documento
    )

    db.add(db_documento)
    db.commit()
    db.refresh(db_documento)

    # Guardar archivo físicamente en background
    background_tasks.add_task(_guardar_archivo_fisico, archivo, ruta_archivo)

    return DocumentoResponse.from_orm(db_documento)

@router.get("/documentos/{documento_id}/descargar")
async def descargar_documento(
    documento_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    archivo_path = DOCUMENTOS_DIR / documento.ruta_archivo
    if not archivo_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el sistema de archivos")

    return FileResponse(
        path=archivo_path,
        filename=documento.nombre_original,
        media_type=documento.tipo_mime or 'application/octet-stream'
    )

@router.put("/documentos/{documento_id}", response_model=DocumentoResponse)
async def actualizar_documento(
    documento_id: int,
    documento_update: DocumentoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar metadata de un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Solo el usuario que subió o admin pueden editar
    if documento.usuario_subio_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este documento")

    for field, value in documento_update.model_dump(exclude_unset=True).items():
        setattr(documento, field, value)

    db.commit()
    db.refresh(documento)

    return DocumentoResponse.from_orm(documento)

@router.delete("/documentos/{documento_id}")
async def eliminar_documento(
    documento_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Solo el usuario que subió o admin pueden eliminar
    if documento.usuario_subio_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este documento")

    # Eliminar archivo físico
    archivo_path = DOCUMENTOS_DIR / documento.ruta_archivo
    if archivo_path.exists():
        archivo_path.unlink()

    # Eliminar de BD
    db.delete(documento)
    db.commit()

    return {"message": "Documento eliminado exitosamente"}

# ===== FUNCIONES AUXILIARES =====

async def _reconstruir_rutas(carpeta: Carpeta, db: Session):
    """Reconstruir rutas completas para una carpeta y sus subcarpetas"""
    if carpeta.parent_id:
        parent = db.query(Carpeta).filter(Carpeta.id == carpeta.parent_id).first()
        carpeta.ruta_completa = f"{parent.ruta_completa}/{carpeta.nombre}"
    else:
        carpeta.ruta_completa = carpeta.nombre

    # Actualizar subcarpetas recursivamente
    for subcarpeta in carpeta.subcarpetas:
        await _reconstruir_rutas(subcarpeta, db)

async def _guardar_archivo_fisico(archivo: UploadFile, ruta_archivo: str):
    """Guardar archivo físicamente en el sistema de archivos"""
    try:
        archivo_path = DOCUMENTOS_DIR / ruta_archivo
        archivo_path.parent.mkdir(parents=True, exist_ok=True)

        with open(archivo_path, "wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
    except Exception as e:
        # En caso de error, podríamos implementar rollback del documento en BD
        print(f"Error guardando archivo {ruta_archivo}: {e}")

# ===== ENDPOINTS DE AUTOMATIZACIÓN =====

@router.post("/automatizacion/crear-carpetas-mes", response_model=dict)
async def crear_carpetas_mes_actual(
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Crear automáticamente la estructura de carpetas para el mes actual"""
    resultado = DocumentosService.crear_carpetas_mes_actual(db)
    return resultado

@router.post("/automatizacion/verificar-estructura", response_model=dict)
async def verificar_estructura_carpetas(
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Verificar la integridad de la estructura de carpetas"""
    resultado = DocumentosService.verificar_estructura_carpetas(db)
    return resultado

@router.post("/automatizacion/limpiar-carpetas-vacias", response_model=dict)
async def limpiar_carpetas_vacias(
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Limpiar carpetas manuales vacías"""
    resultado = DocumentosService.limpiar_carpetas_vacias(db)
    return resultado
