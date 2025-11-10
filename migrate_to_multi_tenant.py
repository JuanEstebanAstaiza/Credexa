"""
Script de migración para convertir el sistema existente a arquitectura multi-tenant SaaS
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import engine, Base, get_db
from app.models import Empresa, Usuario, Rol, Cliente, Prestamo, Pago, Socio, PagoSocio, Carpeta, Documento, Configuracion, SolicitudPassword

def migrate_to_multi_tenant():
    """
    Migra el sistema existente a arquitectura multi-tenant
    """
    print("🚀 INICIANDO MIGRACIÓN A ARQUITECTURA MULTI-TENANT")
    print("=" * 60)

    # Crear una sesión
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Crear la primera empresa (empresa por defecto)
        print("📍 Paso 1: Creando empresa por defecto...")
        empresa_default = Empresa(
            nombre="Credexa - Empresa Principal",
            slug="credexa-principal",
            email="admin@credexa.com",
            telefono="+57 300 123 4567",
            direccion="Colombia",
            activo=True
        )
        db.add(empresa_default)
        db.flush()  # Para obtener el ID

        print(f"✅ Empresa creada: {empresa_default.nombre} (ID: {empresa_default.id})")

        # 2. Actualizar todos los usuarios existentes para que pertenezcan a la empresa por defecto
        print("📍 Paso 2: Migrando usuarios...")
        usuarios_count = db.query(Usuario).update({"empresa_id": empresa_default.id})
        print(f"✅ {usuarios_count} usuarios migrados")

        # 3. Actualizar clientes
        print("📍 Paso 3: Migrando clientes...")
        clientes_count = db.query(Cliente).update({"empresa_id": empresa_default.id})
        print(f"✅ {clientes_count} clientes migrados")

        # 4. Actualizar préstamos
        print("📍 Paso 4: Migrando préstamos...")
        prestamos_count = db.query(Prestamo).update({"empresa_id": empresa_default.id})
        print(f"✅ {prestamos_count} préstamos migrados")

        # 5. Actualizar pagos
        print("📍 Paso 5: Migrando pagos...")
        pagos_count = db.query(Pago).update({"empresa_id": empresa_default.id})
        print(f"✅ {pagos_count} pagos migrados")

        # 6. Actualizar socios
        print("📍 Paso 6: Migrando socios...")
        socios_count = db.query(Socio).update({"empresa_id": empresa_default.id})
        print(f"✅ {socios_count} socios migrados")

        # 7. Actualizar pagos de socio
        print("📍 Paso 7: Migrando pagos de socio...")
        pagos_socio_count = db.query(PagoSocio).update({"empresa_id": empresa_default.id})
        print(f"✅ {pagos_socio_count} pagos de socio migrados")

        # 8. Actualizar carpetas
        print("📍 Paso 8: Migrando carpetas...")
        carpetas_count = db.query(Carpeta).update({"empresa_id": empresa_default.id})
        print(f"✅ {carpetas_count} carpetas migradas")

        # 9. Actualizar documentos
        print("📍 Paso 9: Migrando documentos...")
        documentos_count = db.query(Documento).update({"empresa_id": empresa_default.id})
        print(f"✅ {documentos_count} documentos migrados")

        # 10. Actualizar configuraciones
        print("📍 Paso 10: Migrando configuraciones...")
        configuraciones_count = db.query(Configuracion).update({"empresa_id": empresa_default.id})
        print(f"✅ {configuraciones_count} configuraciones migradas")

        # 11. Actualizar solicitudes de contraseña
        print("📍 Paso 11: Migrando solicitudes de contraseña...")
        solicitudes_count = db.query(SolicitudPassword).update({"empresa_id": empresa_default.id})
        print(f"✅ {solicitudes_count} solicitudes de contraseña migradas")

        # Confirmar todos los cambios
        db.commit()

        print("\n" + "=" * 60)
        print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print(f"🏢 Empresa por defecto creada: {empresa_default.nombre}")
        print(f"📊 ID de empresa: {empresa_default.id}")
        print("🔐 Todos los datos existentes ahora pertenecen a esta empresa")
        print("\n📋 Resumen de migración:")
        print(f"   👥 Usuarios: {usuarios_count}")
        print(f"   🏠 Clientes: {clientes_count}")
        print(f"   💰 Préstamos: {prestamos_count}")
        print(f"   💳 Pagos: {pagos_count}")
        print(f"   👤 Socios: {socios_count}")
        print(f"   💸 Pagos Socio: {pagos_socio_count}")
        print(f"   📁 Carpetas: {carpetas_count}")
        print(f"   📄 Documentos: {documentos_count}")
        print(f"   ⚙️ Configuraciones: {configuraciones_count}")
        print(f"   🔑 Solicitudes: {solicitudes_count}")

        print("\n✅ El sistema está listo para arquitectura multi-tenant!")
        print("🚀 Ahora puedes crear nuevas empresas independientes.")

    except Exception as e:
        db.rollback()
        print(f"❌ ERROR durante la migración: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("⚠️  ADVERTENCIA: Esta migración convertirá el sistema actual a multi-tenant.")
    print("⚠️  Todos los datos existentes pasarán a pertenecer a la empresa por defecto.")
    print("⚠️  Esta operación NO se puede deshacer.")
    print()

    respuesta = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
    if respuesta.upper() == 'SI':
        migrate_to_multi_tenant()
    else:
        print("❌ Migración cancelada por el usuario.")
