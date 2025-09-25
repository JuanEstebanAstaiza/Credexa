"""
Script de migración para agregar funcionalidad de socios
Agrega las nuevas tablas y modifica las existentes
"""

from sqlalchemy import text, MetaData, Table, Column, Integer, String, Numeric
from app.core.database import engine

def migrate_database():
    """Realiza las migraciones necesarias para la funcionalidad de socios"""

    print("🚀 Iniciando migración de socios...")

    try:
        with engine.connect() as conn:
            # Verificar estructura actual de la tabla prestamos
            print("Verificando tabla prestamos...")
            result = conn.execute(text("SELECT name FROM pragma_table_info('prestamos') WHERE name IN ('socio_id', 'origen')"))
            existing_columns = [row[0] for row in result.fetchall()]

            # Agregar columna socio_id si no existe
            if 'socio_id' not in existing_columns:
                print("Agregando columna socio_id...")
                conn.execute(text("ALTER TABLE prestamos ADD COLUMN socio_id INTEGER"))
                conn.commit()
                print("✅ Columna socio_id agregada")

            # Agregar columna origen si no existe
            if 'origen' not in existing_columns:
                print("Agregando columna origen...")
                conn.execute(text("ALTER TABLE prestamos ADD COLUMN origen VARCHAR(20) DEFAULT 'empresa'"))
                conn.commit()
                print("✅ Columna origen agregada")

            # Verificar que las nuevas tablas existen
            print("Verificando tablas de socios...")
            tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('socios', 'pagos_socio')"))
            existing_tables = [row[0] for row in tables_result.fetchall()]

            if 'socios' not in existing_tables:
                print("❌ Tabla socios no encontrada. Ejecuta primero: python -c 'from app.core.database import Base; Base.metadata.create_all()'")
                return

            if 'pagos_socio' not in existing_tables:
                print("❌ Tabla pagos_socio no encontrada. Ejecuta primero: python -c 'from app.core.database import Base; Base.metadata.create_all()'")
                return

            print("✅ Todas las tablas existen")

            # Crear algunos socios de ejemplo
            print("Creando socios de ejemplo...")
            socios_ejemplo = [
                {
                    "nombre_completo": "Ana María López García",
                    "cedula": "11111111",
                    "telefono": "3001111111",
                    "email": "ana.lopez@email.com",
                    "capital_inicial": 10000000,
                    "capital_actual": 12000000,
                    "porcentaje_participacion": 25.0
                },
                {
                    "nombre_completo": "Roberto Carlos Mendoza",
                    "cedula": "22222222",
                    "telefono": "3012222222",
                    "email": "roberto.mendoza@email.com",
                    "capital_inicial": 15000000,
                    "capital_actual": 18000000,
                    "porcentaje_participacion": 35.0
                },
                {
                    "nombre_completo": "Patricia Elena Ruiz",
                    "cedula": "33333333",
                    "telefono": "3023333333",
                    "email": "patricia.ruiz@email.com",
                    "capital_inicial": 8000000,
                    "capital_actual": 9500000,
                    "porcentaje_participacion": 20.0
                }
            ]

            for socio_data in socios_ejemplo:
                # Verificar si ya existe
                exists = conn.execute(text(f"SELECT id FROM socios WHERE cedula = '{socio_data['cedula']}'")).fetchone()
                if not exists:
                    conn.execute(text(f"""
                        INSERT INTO socios (
                            nombre_completo, cedula, telefono, email,
                            capital_inicial, capital_actual, porcentaje_participacion,
                            activo, creado_en, actualizado_en
                        ) VALUES (
                            '{socio_data['nombre_completo']}',
                            '{socio_data['cedula']}',
                            '{socio_data['telefono']}',
                            '{socio_data['email']}',
                            {socio_data['capital_inicial']},
                            {socio_data['capital_actual']},
                            {socio_data['porcentaje_participacion']},
                            1,
                            datetime('now'),
                            datetime('now')
                        )
                    """))
                    conn.commit()
                    print(f"✅ Socio creado: {socio_data['nombre_completo']}")

            print("✅ Migración completada exitosamente!")
            print("\n📋 Resumen de cambios:")
            print("  • Nueva tabla: socios")
            print("  • Nueva tabla: pagos_socio")
            print("  • Columna agregada a prestamos: socio_id")
            print("  • Columna agregada a prestamos: origen")
            print("  • 3 socios de ejemplo creados")
            print("\n🎯 La funcionalidad de socios está lista para usar!")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_database()
