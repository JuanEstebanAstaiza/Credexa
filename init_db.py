"""
Script de inicialización de la base de datos
Crea roles y usuarios iniciales para el sistema
"""

from app.core.database import SessionLocal, engine, Base
from app.models.user import Usuario, Rol
from app.models.cliente import Cliente
from app.models.configuracion import Configuracion as ConfiguracionModel
from app.core.security import get_password_hash

def init_database():
    """Inicializa la base de datos con datos básicos"""

    # Crear tablas
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Verificar si ya existen roles
        existing_roles = db.query(Rol).count()
        if existing_roles > 0:
            print("La base de datos ya está inicializada.")
            return

        print("Inicializando base de datos...")

        # Crear roles
        admin_role = Rol(
            nombre="Administrador",
            descripcion="Usuario con acceso completo al sistema"
        )

        digitador_role = Rol(
            nombre="Digitador",
            descripcion="Usuario con permisos limitados para registro de datos"
        )

        db.add(admin_role)
        db.add(digitador_role)
        db.commit()
        db.refresh(admin_role)
        db.refresh(digitador_role)

        print(f"Roles creados: {admin_role.nombre}, {digitador_role.nombre}")

        # Crear usuario administrador por defecto
        admin_user = Usuario(
            nombre_completo="Administrador del Sistema",
            username="admin",
            email="admin@prestamos.com",
            hashed_password=get_password_hash("admin123"),
            rol_id=admin_role.id
        )

        db.add(admin_user)
        db.commit()

        print("Usuario administrador creado:")
        print("  Usuario: admin")
        print("  Contraseña: admin123")
        print("  Email: admin@prestamos.com")

        # Crear usuario digitador de ejemplo
        digitador_user = Usuario(
            nombre_completo="Digitador de Ejemplo",
            username="digitador",
            email="digitador@prestamos.com",
            hashed_password=get_password_hash("digitador123"),
            rol_id=digitador_role.id
        )

        db.add(digitador_user)
        db.commit()

        print("Usuario digitador creado:")
        print("  Usuario: digitador")
        print("  Contraseña: digitador123")
        print("  Email: digitador@prestamos.com")

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

        # Crear configuraciones por defecto
        configuraciones_default = [
            {
                "clave": "tasa_interes_default",
                "valor": "2.5",
                "tipo": "float",
                "categoria": "financiero",
                "descripcion": "Tasa de interés por defecto para nuevos préstamos (%)"
            },
            {
                "clave": "monto_maximo_prestamo",
                "valor": "50000000",
                "tipo": "int",
                "categoria": "financiero",
                "descripcion": "Monto máximo permitido para un préstamo"
            },
            {
                "clave": "dias_gracia",
                "valor": "3",
                "tipo": "int",
                "categoria": "financiero",
                "descripcion": "Días de gracia para pagos sin penalización"
            },
            {
                "clave": "email_notificaciones",
                "valor": "admin@empresa.com",
                "tipo": "string",
                "categoria": "notificaciones",
                "descripcion": "Email para recibir notificaciones del sistema"
            },
            {
                "clave": "registros_por_pagina",
                "valor": "10",
                "tipo": "int",
                "categoria": "general",
                "descripcion": "Número de registros a mostrar por página"
            },
            {
                "clave": "zona_horaria",
                "valor": "America/Bogota",
                "tipo": "string",
                "categoria": "general",
                "descripcion": "Zona horaria del sistema"
            },
            {
                "clave": "moneda_default",
                "valor": "COP",
                "tipo": "string",
                "categoria": "general",
                "descripcion": "Código de moneda por defecto"
            },
            {
                "clave": "sesion_timeout_minutos",
                "valor": "60",
                "tipo": "int",
                "categoria": "seguridad",
                "descripcion": "Tiempo de expiración de sesión en minutos"
            }
        ]

        for config_data in configuraciones_default:
            configuracion = ConfiguracionModel(**config_data)
            db.add(configuracion)

        db.commit()
        print("Configuraciones por defecto creadas:")
        for config_data in configuraciones_default:
            print(f"  - {config_data['clave']}: {config_data['valor']}")

        print("\nBase de datos inicializada exitosamente!")
        print("Puedes iniciar sesión con las credenciales de arriba.")
        print("También se crearon 3 clientes y configuraciones por defecto.")

    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
