import os
import shutil
import sqlite3
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import Usuario
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Directorio para almacenar backups
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

# Directorios a incluir en backup completo
BACKUP_DIRECTORIES = [
    "instance",      # Bases de datos
    "documentos",    # Sistema de gestión documental
    "app/static/uploads",  # Archivos subidos (si existe)
    "logs",          # Logs del sistema (si existe)
    "backups"        # Backups existentes
]

# Archivos específicos a incluir
BACKUP_FILES = [
    ".env",          # Variables de entorno
    "requirements.txt",  # Dependencias
    "README.md",     # Documentación
    ".gitignore"     # Configuración git
]

@router.get("/listar", response_model=List[Dict])
async def listar_backups(
    current_user: Usuario = Depends(get_current_admin_user)
) -> List[Dict]:
    """
    Lista todos los backups disponibles
    """
    try:
        backups = []
        # Buscar archivos .zip (backups completos)
        for backup_file in BACKUP_DIR.glob("*.zip"):
            if backup_file.is_file():
                stat = backup_file.stat()
                # Verificar si es un backup válido (contiene backup completo)
                try:
                    with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        has_database = any('instance/' in f and f.endswith('.db') for f in file_list)
                        has_documents = any('documentos/' in f for f in file_list)
                        backup_type = "completo" if has_database and has_documents else "parcial"
                except:
                    backup_type = "desconocido"

                backups.append({
                    "filename": backup_file.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size_human": f"{stat.st_size / (1024*1024):.2f} MB",
                    "type": backup_type,
                    "is_complete": backup_type == "completo"
                })

        # También buscar archivos .db antiguos para compatibilidad
        for backup_file in BACKUP_DIR.glob("*.db"):
            if backup_file.is_file() and not backup_file.name.startswith('temp_') and not backup_file.name.startswith('security_backup_'):
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size_human": f"{stat.st_size / (1024*1024):.2f} MB",
                    "type": "base_datos",
                    "is_complete": False
                })

        # Ordenar por fecha de creación (más reciente primero)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        raise HTTPException(status_code=500, detail="Error al listar backups")

def create_complete_backup(backup_filename: str, backup_path: Path):
    """
    Crea un backup completo del sistema incluyendo:
    - Base de datos
    - Sistema de gestión documental
    - Archivos subidos
    - Configuraciones
    - Logs
    """
    try:
        logger.info(f"Iniciando creación de backup completo: {backup_filename}")

        # Crear directorio temporal para preparar el backup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            logger.info(f"Directorio temporal creado: {temp_path}")

            # 1. Copiar base de datos
            from app.core.config import settings
            DATABASE_URL = settings.DATABASE_URL
            if DATABASE_URL.startswith("sqlite:///"):
                db_path = DATABASE_URL.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    db_dest = temp_path / "instance" / Path(db_path).name
                    db_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(db_path, db_dest)
                    logger.info(f"Base de datos copiada: {db_path} -> {db_dest}")
                else:
                    logger.warning(f"Base de datos no encontrada: {db_path}")
            else:
                logger.warning("Tipo de base de datos no soportado para backup completo")

            # 2. Copiar directorios importantes
            for dir_name in BACKUP_DIRECTORIES:
                src_dir = Path(dir_name)
                if src_dir.exists() and src_dir.is_dir():
                    dest_dir = temp_path / dir_name
                    try:
                        shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
                        logger.info(f"Directorio copiado: {src_dir} -> {dest_dir}")
                    except Exception as e:
                        logger.warning(f"Error copiando directorio {src_dir}: {e}")

            # 3. Copiar archivos específicos
            for file_name in BACKUP_FILES:
                src_file = Path(file_name)
                if src_file.exists() and src_file.is_file():
                    dest_file = temp_path / file_name
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    logger.info(f"Archivo copiado: {src_file} -> {dest_file}")

            # 4. Crear archivo ZIP con todo el contenido
            logger.info(f"Creando archivo ZIP: {backup_path}")
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        # Calcular ruta relativa para el ZIP
                        relative_path = file_path.relative_to(temp_path)
                        zip_ref.write(file_path, relative_path)
                        logger.debug(f"Agregado al ZIP: {relative_path}")

            # Verificar el backup creado
            if backup_path.exists():
                size_mb = backup_path.stat().st_size / (1024 * 1024)
                logger.info(f"Backup creado exitosamente: {size_mb:.2f} MB")
            else:
                raise Exception("Backup no se creó correctamente")

    except Exception as e:
        logger.error(f"Error creando backup completo: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Limpiar archivo si falló
        if backup_path.exists():
            backup_path.unlink()
        raise

@router.post("/crear")
async def crear_backup(
    background_tasks: BackgroundTasks,
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea un backup completo del sistema ERP
    """
    try:
        # Generar nombre del backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_completo_{timestamp}.zip"
        backup_path = BACKUP_DIR / backup_filename

        # Verificar permisos de escritura
        if not BACKUP_DIR.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de backups creado: {BACKUP_DIR}")

        def create_backup_task():
            try:
                create_complete_backup(backup_filename, backup_path)
            except Exception as e:
                logger.error(f"Error en tarea de backup: {e}")

        # Ejecutar backup en background
        background_tasks.add_task(create_backup_task)

        return {
            "message": "Backup completo en proceso",
            "filename": backup_filename,
            "status": "processing",
            "description": "Incluye base de datos, documentos, archivos y configuraciones"
        }

    except Exception as e:
        logger.error(f"Error iniciando backup: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al crear backup: {str(e)}")

@router.post("/crear-db")
async def crear_backup_db(
    background_tasks: BackgroundTasks,
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea un backup solo de la base de datos (modo legacy)
    """
    try:
        # Generar nombre del backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_db_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename

        # Obtener la ruta de la base de datos actual
        from app.core.config import settings
        DATABASE_URL = settings.DATABASE_URL
        if DATABASE_URL.startswith("sqlite:///"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            logger.info(f"Ruta de base de datos: {db_path}")
            if not os.path.exists(db_path):
                logger.error(f"Base de datos no encontrada en: {db_path}")
                raise HTTPException(status_code=500, detail=f"Base de datos no encontrada: {db_path}")
        else:
            logger.error(f"Tipo de base de datos no soportado: {DATABASE_URL}")
            raise HTTPException(status_code=500, detail="Solo se soportan bases de datos SQLite")

        # Crear backup usando sqlite3
        def create_backup():
            try:
                logger.info(f"Iniciando creación de backup DB: {backup_filename}")

                # Conectar a la base de datos original
                conn_source = sqlite3.connect(db_path)
                logger.info("Conexión a base de datos origen exitosa")

                # Crear backup
                conn_backup = sqlite3.connect(str(backup_path))
                logger.info("Conexión a backup creada")

                conn_source.backup(conn_backup)
                logger.info("Backup realizado exitosamente")

                conn_backup.close()
                conn_source.close()
                logger.info(f"Backup DB creado exitosamente: {backup_filename}")

            except Exception as e:
                logger.error(f"Error creando backup DB: {e}")
                logger.error(f"Tipo de error: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Limpiar archivo si falló
                if backup_path.exists():
                    backup_path.unlink()

        # Ejecutar backup en background
        background_tasks.add_task(create_backup)

        return {
            "message": "Backup de base de datos en proceso",
            "filename": backup_filename,
            "status": "processing",
            "description": "Solo incluye la base de datos SQLite"
        }

    except Exception as e:
        logger.error(f"Error iniciando backup DB: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al crear backup: {str(e)}")

@router.get("/descargar/{filename}")
async def descargar_backup(
    filename: str,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Descarga un backup específico
    """
    try:
        backup_path = BACKUP_DIR / filename

        # Validar que el archivo existe
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup no encontrado")

        # Validar que sea un archivo .db o .zip
        if not (filename.endswith('.db') or filename.endswith('.zip')):
            raise HTTPException(status_code=400, detail="Archivo no válido")

        # Validar que esté en el directorio de backups
        if not backup_path.is_file():
            raise HTTPException(status_code=404, detail="Backup no encontrado")

        # Determinar tipo MIME basado en extensión
        media_type = 'application/zip' if filename.endswith('.zip') else 'application/octet-stream'

        return FileResponse(
            path=str(backup_path),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando backup: {e}")
        raise HTTPException(status_code=500, detail="Error al descargar backup")

def restore_complete_backup(zip_path: Path):
    """
    Restaura un backup completo desde archivo ZIP
    """
    try:
        logger.info(f"Iniciando restauración completa desde: {zip_path}")

        # Crear directorio temporal para extraer
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            logger.info(f"Directorio temporal creado: {temp_path}")

            # Extraer el ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
                logger.info("ZIP extraído correctamente")

            # Lista de archivos/directorios a restaurar
            restore_items = [
                ("instance", "Bases de datos"),
                ("documentos", "Sistema de gestión documental"),
                ("app/static/uploads", "Archivos subidos"),
                ("logs", "Archivos de log"),
                ("backups", "Backups existentes"),
                (".env", "Variables de entorno"),
                ("requirements.txt", "Dependencias"),
                ("README.md", "Documentación")
            ]

            restored_items = []

            # Restaurar directorios
            for item, description in restore_items:
                src_path = temp_path / item
                dest_path = Path(item)

                if src_path.exists():
                    try:
                        if src_path.is_file():
                            # Es un archivo
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_path, dest_path)
                            restored_items.append(f"📄 {description}")
                            logger.info(f"Archivo restaurado: {dest_path}")
                        elif src_path.is_dir():
                            # Es un directorio
                            if dest_path.exists():
                                shutil.rmtree(dest_path)
                            shutil.copytree(src_path, dest_path)
                            restored_items.append(f"📁 {description}")
                            logger.info(f"Directorio restaurado: {dest_path}")
                    except Exception as e:
                        logger.warning(f"Error restaurando {item}: {e}")

            # Verificar si se restauró la base de datos
            db_restored = False
            for db_file in temp_path.glob("instance/*.db"):
                if db_file.exists():
                    db_restored = True
                    break

            return {
                "success": True,
                "restored_items": restored_items,
                "database_restored": db_restored,
                "message": f"Restauración completa exitosa. Elementos restaurados: {len(restored_items)}"
            }

    except Exception as e:
        logger.error(f"Error en restauración completa: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error durante la restauración completa"
        }

@router.post("/restaurar")
async def restaurar_backup(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Restaura un backup desde un archivo subido (soporta .db y .zip)
    """
    try:
        # Validar tipo de archivo
        if not (file.filename.endswith('.db') or file.filename.endswith('.zip')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos .db o .zip")

        # Validar tamaño del archivo (máximo 30GB para ambos tipos)
        max_size = 30 * 1024 * 1024 * 1024  # 30GB en bytes
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máximo 30GB)")

        is_complete_backup = file.filename.endswith('.zip')

        if is_complete_backup:
            # Restauración completa desde ZIP
            temp_backup_path = BACKUP_DIR / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

            try:
                # Guardar archivo temporalmente
                with open(temp_backup_path, 'wb') as f:
                    f.write(file_content)

                # Validar que sea un ZIP válido y contenga elementos esperados
                with zipfile.ZipFile(temp_backup_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    has_database = any('instance/' in f and f.endswith('.db') for f in file_list)
                    if not has_database:
                        raise HTTPException(
                            status_code=400,
                            detail="Backup incompleto: no contiene base de datos"
                        )

            except zipfile.BadZipFile:
                # Limpiar archivo temporal
                if temp_backup_path.exists():
                    temp_backup_path.unlink()
                raise HTTPException(status_code=400, detail="Archivo ZIP inválido o corrupto")

            def restore_complete():
                try:
                    result = restore_complete_backup(temp_backup_path)

                    # Limpiar archivo temporal
                    temp_backup_path.unlink()

                    if result["success"]:
                        logger.info(f"Restauración completa exitosa desde {file.filename}")
                    else:
                        logger.error(f"Error en restauración completa: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    logger.error(f"Error en tarea de restauración completa: {e}")
                    # Limpiar archivo temporal
                    if temp_backup_path.exists():
                        temp_backup_path.unlink()

            # Ejecutar restauración completa en background
            background_tasks.add_task(restore_complete)

            return {
                "message": "Restauración completa en proceso",
                "filename": file.filename,
                "status": "processing",
                "type": "complete",
                "description": "Restaurará base de datos, documentos y configuraciones"
            }

        else:
            # Restauración solo de base de datos (modo legacy)
            temp_backup_path = BACKUP_DIR / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

            try:
                # Guardar archivo temporalmente
                with open(temp_backup_path, 'wb') as f:
                    f.write(file_content)

                # Validar que sea una base de datos SQLite válida
                conn = sqlite3.connect(str(temp_backup_path))
                cursor = conn.cursor()

                # Verificar tablas principales
                required_tables = ['clientes', 'prestamos', 'pagos', 'socios', 'pagos_socio', 'usuarios']
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]

                missing_tables = [table for table in required_tables if table not in existing_tables]
                if missing_tables:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Backup inválido: faltan tablas {', '.join(missing_tables)}"
                    )

                conn.close()

            except sqlite3.Error as e:
                # Limpiar archivo temporal
                if temp_backup_path.exists():
                    temp_backup_path.unlink()
                raise HTTPException(status_code=400, detail=f"Archivo no es una base de datos SQLite válida: {str(e)}")

            # Obtener la ruta de la base de datos actual
            from app.core.config import settings
            DATABASE_URL = settings.DATABASE_URL
            if DATABASE_URL.startswith("sqlite:///"):
                db_path = DATABASE_URL.replace("sqlite:///", "")
            else:
                raise HTTPException(status_code=500, detail="Solo se soportan bases de datos SQLite")

            # Crear backup de seguridad antes de restaurar
            security_backup_name = f"security_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            security_backup_path = BACKUP_DIR / security_backup_name

            def restore_db():
                try:
                    # Crear backup de seguridad
                    conn_source = sqlite3.connect(db_path)
                    conn_security = sqlite3.connect(str(security_backup_path))
                    conn_source.backup(conn_security)
                    conn_security.close()
                    conn_source.close()

                    # Restaurar desde el backup subido
                    conn_restore = sqlite3.connect(str(temp_backup_path))
                    conn_target = sqlite3.connect(db_path)

                    # Limpiar base de datos actual
                    cursor = conn_target.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    for table in tables:
                        if table[0] != 'sqlite_sequence':  # No eliminar metadatos
                            cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")

                    # Restaurar desde backup
                    conn_restore.backup(conn_target)
                    conn_target.commit()
                    conn_target.close()
                    conn_restore.close()

                    # Limpiar archivo temporal
                    temp_backup_path.unlink()

                    logger.info(f"Backup DB restaurado exitosamente desde {file.filename}")

                except Exception as e:
                    logger.error(f"Error restaurando backup DB: {e}")
                    # Limpiar archivos temporales
                    if temp_backup_path.exists():
                        temp_backup_path.unlink()
                    raise

            # Ejecutar restauración de DB en background
            background_tasks.add_task(restore_db)

            return {
                "message": "Restauración de base de datos en proceso",
                "filename": file.filename,
                "security_backup": security_backup_name,
                "status": "processing",
                "type": "database_only",
                "description": "Solo restaurará la base de datos SQLite"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error iniciando restauración: {e}")
        raise HTTPException(status_code=500, detail="Error al restaurar backup")

@router.delete("/{filename}")
async def eliminar_backup(
    filename: str,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Elimina un backup específico
    """
    try:
        backup_path = BACKUP_DIR / filename

        # Validar que el archivo existe
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup no encontrado")

        # Validar que sea un archivo .db o .zip
        if not (filename.endswith('.db') or filename.endswith('.zip')):
            raise HTTPException(status_code=400, detail="Archivo no válido")

        # No permitir eliminar backups de seguridad automáticos
        if filename.startswith('security_backup_') or filename.startswith('temp_restore_'):
            raise HTTPException(status_code=400, detail="No se pueden eliminar backups de seguridad automáticos")

        # Eliminar archivo
        backup_path.unlink()

        return {"message": f"Backup {filename} eliminado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando backup: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar backup")

@router.get("/estadisticas")
async def estadisticas_backup(
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Estadísticas de backups
    """
    try:
        complete_backups = 0
        db_backups = 0
        total_size = 0
        total_backups = 0

        # Contar backups ZIP completos
        for backup_file in BACKUP_DIR.glob("*.zip"):
            if backup_file.is_file():
                stat = backup_file.stat()
                total_size += stat.st_size
                total_backups += 1
                complete_backups += 1

        # Contar backups DB legacy
        for backup_file in BACKUP_DIR.glob("*.db"):
            if backup_file.is_file() and not backup_file.name.startswith('temp_') and not backup_file.name.startswith('security_backup_'):
                stat = backup_file.stat()
                total_size += stat.st_size
                total_backups += 1
                db_backups += 1

        return {
            "total_backups": total_backups,
            "complete_backups": complete_backups,
            "database_backups": db_backups,
            "total_size_bytes": total_size,
            "total_size_human": f"{total_size / (1024*1024):.2f} MB",
            "backup_directory": str(BACKUP_DIR),
            "included_directories": BACKUP_DIRECTORIES,
            "included_files": BACKUP_FILES
        }

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")
