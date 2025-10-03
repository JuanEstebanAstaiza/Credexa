#!/usr/bin/env python3
"""
Script para limpiar completamente el sistema ERP y dejarlo listo para producción
"""
import os
import shutil
from pathlib import Path
import sqlite3
from datetime import datetime

def limpiar_sistema():
    print("🧹 LIMPIEZA COMPLETA DEL SISTEMA ERP PARA PRODUCCIÓN")
    print("=" * 60)

    base_dir = Path.cwd()

    # 1. Limpiar directorio de documentos
    documentos_dir = base_dir / "documentos"
    if documentos_dir.exists():
        print("📁 Eliminando directorio de gestión documental...")
        try:
            shutil.rmtree(documentos_dir)
            print("✅ Directorio 'documentos' eliminado")
        except Exception as e:
            print(f"❌ Error eliminando documentos: {e}")
    else:
        print("ℹ️ Directorio 'documentos' no existe")

    # 2. Limpiar directorio de backups
    backups_dir = base_dir / "backups"
    if backups_dir.exists():
        print("🗂️ Limpiando directorio de backups...")
        try:
            shutil.rmtree(backups_dir)
            backups_dir.mkdir(exist_ok=True)
            print("✅ Directorio 'backups' limpiado y recreado")
        except Exception as e:
            print(f"❌ Error limpiando backups: {e}")
    else:
        print("ℹ️ Directorio 'backups' no existe")

    # 3. Limpiar archivos temporales y de desarrollo
    archivos_a_eliminar = [
        "demo_emails.html",
        "test_email_persistence.py",
        "check_backups.py",
        "check_db.py",
        "check_password.py",
        "check_socios.py",
        "create_clientes_table.py",
        "create_prestamos_table.py",
        "migrate_socios.py",
        "test_digitador_flow.py",
        "test_documentos_completo.py",
        "test_documentos.py",
        "test_email_config.py",
        "test_final_flow.py",
        "test_password_flow.py",
        "test_responder_solicitud.py",
        "test_solicitudes.py",
        "verificar_zona_horaria.py"
    ]

    print("🗑️ Eliminando archivos temporales de desarrollo...")
    eliminados = 0
    for archivo in archivos_a_eliminar:
        file_path = base_dir / archivo
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Eliminado: {archivo}")
                eliminados += 1
            except Exception as e:
                print(f"❌ Error eliminando {archivo}: {e}")

    if eliminados == 0:
        print("ℹ️ No se encontraron archivos temporales para eliminar")

    # 4. Resetear base de datos
    instance_dir = base_dir / "instance"
    if instance_dir.exists():
        print("🗄️ Reseteando bases de datos...")

        # Buscar archivos .db en instance
        db_files = list(instance_dir.glob("*.db"))
        for db_file in db_files:
            try:
                print(f"🗑️ Eliminando base de datos: {db_file.name}")
                db_file.unlink()
                print(f"✅ Base de datos {db_file.name} eliminada")
            except Exception as e:
                print(f"❌ Error eliminando {db_file.name}: {e}")

        # Crear base de datos limpia con usuario admin
        prestamos_db = instance_dir / "prestamos.db"
        try:
            print("🏗️ Creando base de datos limpia con usuario admin...")

            conn = sqlite3.connect(str(prestamos_db))
            cursor = conn.cursor()

            # Crear tablas básicas usando SQLAlchemy para asegurar consistencia
            from app.core.database import Base, engine
            from app.models.user import Usuario, Rol
            from app.models.configuracion import Configuracion

            # Crear todas las tablas
            Base.metadata.create_all(bind=engine)

            # Insertar rol admin usando SQLAlchemy
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()

            try:
                # Verificar si ya existe el rol admin
                admin_role = db.query(Rol).filter(Rol.nombre == "admin").first()
                if not admin_role:
                    admin_role = Rol(
                        nombre="admin",
                        descripcion="Administrador del sistema con acceso completo",
                        activo=True
                    )
                    db.add(admin_role)
                    db.commit()

                # Verificar si ya existe el rol digitador
                digitador_role = db.query(Rol).filter(Rol.nombre == "digitador").first()
                if not digitador_role:
                    digitador_role = Rol(
                        nombre="digitador",
                        descripcion="Usuario con permisos limitados para digitación",
                        activo=True
                    )
                    db.add(digitador_role)
                    db.commit()

                # Verificar si ya existe el usuario admin
                admin_user = db.query(Usuario).filter(Usuario.username == "admin").first()
                if admin_user:
                    # Actualizar contraseña y datos
                    from werkzeug.security import generate_password_hash
                    admin_user.hashed_password = generate_password_hash('admin123')
                    admin_user.nombre_completo = 'Administrador'
                    admin_user.email = 'admin@empresa.com'
                    admin_user.activo = True
                    admin_user.rol_id = admin_role.id
                else:
                    # Crear usuario admin
                    from werkzeug.security import generate_password_hash
                    admin_user = Usuario(
                        nombre_completo='Administrador',
                        username='admin',
                        email='admin@empresa.com',
                        hashed_password=generate_password_hash('admin123'),
                        rol_id=admin_role.id,
                        activo=True
                    )
                    db.add(admin_user)

                # Configuraciones básicas
                configs = [
                    ('app_name', 'Credexa', 'string', 'Nombre de la aplicación', 'general'),
                    ('empresa_nombre', 'Credexa SAS', 'string', 'Nombre de la empresa', 'empresa'),
                    ('empresa_email', 'info@credexa.com', 'string', 'Email de la empresa', 'empresa'),
                    ('version', '1.0.0', 'string', 'Versión del sistema', 'sistema')
                ]

                for clave, valor, tipo, desc, cat in configs:
                    config_existente = db.query(Configuracion).filter(Configuracion.clave == clave).first()
                    if not config_existente:
                        nueva_config = Configuracion(
                            clave=clave,
                            valor=valor,
                            tipo=tipo,
                            descripcion=desc,
                            categoria=cat
                        )
                        db.add(nueva_config)

                db.commit()
                print("✅ Base de datos inicializada correctamente con SQLAlchemy")

            except Exception as e:
                db.rollback()
                print(f"❌ Error inicializando base de datos: {e}")
                raise
            finally:
                db.close()

            print("✅ Base de datos limpia creada con usuario admin/admin123")

        except Exception as e:
            print(f"❌ Error creando base de datos limpia: {e}")

    else:
        print("ℹ️ Directorio 'instance' no existe")

    # 5. Limpiar directorios de logs si existen
    logs_dir = base_dir / "logs"
    if logs_dir.exists():
        print("📋 Limpiando directorios de logs...")
        try:
            shutil.rmtree(logs_dir)
            print("✅ Directorio 'logs' eliminado")
        except Exception as e:
            print(f"❌ Error eliminando logs: {e}")

    # 6. Limpiar directorios de uploads si existen
    uploads_dir = base_dir / "app" / "static" / "uploads"
    if uploads_dir.exists():
        print("📤 Limpiando directorios de uploads...")
        try:
            shutil.rmtree(uploads_dir)
            print("✅ Directorio 'uploads' eliminado")
        except Exception as e:
            print(f"❌ Error eliminando uploads: {e}")

    print("\n" + "=" * 60)
    print("🎉 LIMPIEZA COMPLETA FINALIZADA")
    print("=" * 60)
    print("✅ Directorio de documentos eliminado")
    print("✅ Directorio de backups limpiado")
    print("✅ Archivos temporales de desarrollo eliminados")
    print("✅ Bases de datos reseteadas")
    print("✅ Usuario admin recreado (admin/admin123)")
    print("✅ Configuraciones básicas establecidas")
    print("\n🚀 El sistema está listo para producción!")

if __name__ == "__main__":
    print("⚠️  ADVERTENCIA: Esta acción eliminará TODOS los datos actuales")
    print("⚠️  Se creará un sistema completamente limpio")
    print()

    respuesta = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")

    if respuesta.upper() == 'SI':
        limpiar_sistema()
    else:
        print("❌ Operación cancelada por el usuario")
