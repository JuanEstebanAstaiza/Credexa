"""
Script para crear la tabla de clientes en la base de datos existente
"""

from app.core.database import SessionLocal, engine, Base
from app.models.cliente import Cliente
from app.models.user import Usuario, Rol

def create_clientes_table():
    """Crear tabla de clientes y agregar datos de ejemplo"""

    # Crear tabla de clientes
    Cliente.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()

    try:
        # Verificar si ya existen clientes
        existing_clientes = db.query(Cliente).count()
        if existing_clientes > 0:
            print("Los clientes ya están creados en la base de datos.")
            return

        print("Creando tabla de clientes y datos de ejemplo...")

        # Crear clientes de ejemplo
        clientes_ejemplo = [
            {
                "nombre_completo": "Juan Carlos Pérez González",
                "cedula": "12345678",
                "telefono": "3001234567",
                "email": "juan.perez@email.com",
                "direccion": "Calle 10 # 5-20, Bogotá",
                "ocupacion": "Ingeniero",
                "ingresos_mensuales": 3500000,
                "referencias_personales": "María González (hermana) - 3012345678",
                "notas": "Cliente regular, buen historial de pagos"
            },
            {
                "nombre_completo": "María Fernanda López Rodríguez",
                "cedula": "87654321",
                "telefono": "3019876543",
                "email": "maria.lopez@email.com",
                "direccion": "Carrera 15 # 25-30, Medellín",
                "ocupacion": "Profesora",
                "ingresos_mensuales": 2800000,
                "referencias_personales": "Carlos Rodríguez (esposo) - 3023456789",
                "notas": "Primera vez solicitando préstamo"
            },
            {
                "nombre_completo": "Carlos Alberto Ramírez Silva",
                "cedula": "11223344",
                "telefono": "3105556667",
                "email": "carlos.ramirez@email.com",
                "direccion": "Avenida 68 # 45-12, Bogotá",
                "ocupacion": "Comerciante",
                "ingresos_mensuales": 4200000,
                "referencias_personales": "Ana Silva (esposa) - 3112223334",
                "notas": "Cliente con historial de 3 préstamos anteriores"
            }
        ]

        for cliente_data in clientes_ejemplo:
            cliente = Cliente(**cliente_data)
            db.add(cliente)

        db.commit()
        print("Clientes de ejemplo creados:")
        for cliente_data in clientes_ejemplo:
            print(f"  - {cliente_data['nombre_completo']} ({cliente_data['cedula']})")

        print("\nTabla de clientes creada exitosamente!")

    except Exception as e:
        print(f"Error creando tabla de clientes: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_clientes_table()
