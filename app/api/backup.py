import os
import shutil
import sqlite3
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

@router.get("/listar", response_model=List[Dict])
async def listar_backups(
    current_user: Usuario = Depends(get_current_admin_user)
) -> List[Dict]:
    """
    Lista todos los backups disponibles
    """
    try:
        backups = []
        for backup_file in BACKUP_DIR.glob("*.db"):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size_human": f"{stat.st_size / (1024*1024):.2f} MB"
                })

        # Ordenar por fecha de creación (más reciente primero)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        raise HTTPException(status_code=500, detail="Error al listar backups")

@router.post("/crear")
async def crear_backup(
    background_tasks: BackgroundTasks,
    current_user: Usuario = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea un backup completo de la base de datos
    """
    try:
        # Generar nombre del backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
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
                logger.info(f"Iniciando creación de backup: {backup_filename}")
                logger.info(f"Origen: {db_path}")
                logger.info(f"Destino: {backup_path}")

                # Verificar permisos de escritura en directorio de backups
                if not BACKUP_DIR.exists():
                    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Directorio de backups creado: {BACKUP_DIR}")

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
                logger.info(f"Backup creado exitosamente: {backup_filename}")

            except Exception as e:
                logger.error(f"Error creando backup: {e}")
                logger.error(f"Tipo de error: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Limpiar archivo si falló
                if backup_path.exists():
                    backup_path.unlink()

        # Ejecutar backup en background
        background_tasks.add_task(create_backup)

        return {
            "message": "Backup en proceso",
            "filename": backup_filename,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error iniciando backup: {e}")
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

        # Validar que sea un archivo .db
        if not filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Archivo no válido")

        # Validar que esté en el directorio de backups
        if not backup_path.is_file():
            raise HTTPException(status_code=404, detail="Backup no encontrado")

        return FileResponse(
            path=str(backup_path),
            filename=filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando backup: {e}")
        raise HTTPException(status_code=500, detail="Error al descargar backup")

@router.post("/restaurar")
async def restaurar_backup(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Restaura un backup desde un archivo subido
    """
    try:
        # Validar tipo de archivo
        if not file.filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos .db")

        # Validar tamaño del archivo (máximo 100MB)
        file_content = await file.read()
        if len(file_content) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máximo 100MB)")

        # Crear archivo temporal para validación
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

        def restore_backup():
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

                logger.info(f"Backup restaurado exitosamente desde {file.filename}")

            except Exception as e:
                logger.error(f"Error restaurando backup: {e}")
                # Limpiar archivos temporales
                if temp_backup_path.exists():
                    temp_backup_path.unlink()
                raise

        # Ejecutar restauración en background
        background_tasks.add_task(restore_backup)

        return {
            "message": "Restauración en proceso",
            "filename": file.filename,
            "security_backup": security_backup_name,
            "status": "processing"
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

        # Validar que sea un archivo .db
        if not filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Archivo no válido")

        # No permitir eliminar backups de seguridad automáticos
        if filename.startswith('security_backup_'):
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
        backups = []
        total_size = 0
        count = 0

        for backup_file in BACKUP_DIR.glob("*.db"):
            if backup_file.is_file():
                stat = backup_file.stat()
                total_size += stat.st_size
                count += 1

        return {
            "total_backups": count,
            "total_size_bytes": total_size,
            "total_size_human": f"{total_size / (1024*1024):.2f} MB",
            "backup_directory": str(BACKUP_DIR)
        }

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")
