#!/usr/bin/env python3
"""
Script simple de migración multi-tenant
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.core.database import engine, Base, create_tables
from sqlalchemy import text

def migrate_db():
    """Migrar base de datos para multi-tenant"""

    print("Iniciando migracion multi-tenant...")

    # Crear todas las tablas
    create_tables()

    # Ejecutar migraciones SQL manualmente
    with engine.connect() as conn:
        # Agregar columna empresa_id a todas las tablas
        tables_to_migrate = [
            'usuarios', 'clientes', 'prestamos', 'pagos', 'socios',
            'pagos_socio', 'carpetas', 'documentos', 'configuraciones', 'solicitudes_password'
        ]

        for table in tables_to_migrate:
            try:
                # Verificar si la columna ya existe
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result.fetchall()]

                if 'empresa_id' not in columns:
                    print(f"Agregando empresa_id a tabla {table}...")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN empresa_id INTEGER"))
                    conn.commit()
                else:
                    print(f"Tabla {table} ya tiene empresa_id")
            except Exception as e:
                print(f"Error migrando tabla {table}: {e}")

        # Crear tablas nuevas
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(255) NOT NULL,
                    slug VARCHAR(100) UNIQUE NOT NULL,
                    dominio VARCHAR(255),
                    email VARCHAR(255) NOT NULL,
                    telefono VARCHAR(50),
                    direccion TEXT,
                    configuracion TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME
                )
            """))
        except Exception as e:
            print(f"Error creando tabla empresas: {e}")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS planes_suscripcion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(100) NOT NULL,
                    slug VARCHAR(100) UNIQUE NOT NULL,
                    descripcion TEXT,
                    precio_mensual FLOAT NOT NULL,
                    precio_anual FLOAT,
                    max_usuarios INTEGER DEFAULT 1,
                    max_clientes INTEGER DEFAULT 100,
                    max_prestamos_activos INTEGER DEFAULT 50,
                    almacenamiento_gb INTEGER DEFAULT 1,
                    soporte_premium BOOLEAN DEFAULT 0,
                    reportes_avanzados BOOLEAN DEFAULT 0,
                    api_access BOOLEAN DEFAULT 0,
                    integraciones BOOLEAN DEFAULT 0,
                    backup_automatico BOOLEAN DEFAULT 1,
                    activo BOOLEAN DEFAULT 1,
                    popular BOOLEAN DEFAULT 0,
                    orden INTEGER DEFAULT 0,
                    configuracion_extra TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME
                )
            """))
        except Exception as e:
            print(f"Error creando tabla planes_suscripcion: {e}")

        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS suscripciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    plan_id INTEGER NOT NULL,
                    estado VARCHAR(20) DEFAULT 'activa',
                    tipo VARCHAR(20) DEFAULT 'mensual',
                    precio_pagado FLOAT NOT NULL,
                    metodo_pago VARCHAR(50),
                    referencia_pago VARCHAR(100),
                    renovacion_automatica BOOLEAN DEFAULT 1,
                    limite_usuarios INTEGER,
                    limite_clientes INTEGER,
                    limite_prestamos INTEGER,
                    limite_almacenamiento_gb INTEGER,
                    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin DATETIME,
                    fecha_cancelacion DATETIME,
                    fecha_suspension DATETIME,
                    observaciones TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id),
                    FOREIGN KEY (plan_id) REFERENCES planes_suscripcion (id)
                )
            """))
        except Exception as e:
            print(f"Error creando tabla suscripciones: {e}")

        conn.commit()

    print("Migracion completada!")

if __name__ == "__main__":
    migrate_db()
