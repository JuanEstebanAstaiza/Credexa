#!/usr/bin/env python3
"""
Script para resetear completamente la base de datos y llenarla con datos limpios
para probar todas las funcionalidades del sistema.
"""

import os
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user import Usuario, Rol
from app.models.cliente import Cliente
from app.models.socio import Socio
from app.models.prestamo import Prestamo
from app.models.pago import Pago
from app.models.pago_socio import PagoSocio
from app.models.configuracion import Configuracion
from app.models.carpeta import Carpeta
from app.models.documento import Documento

from app.core.security import get_password_hash

def reset_database():
    """Vacía completamente la base de datos y recrea todas las tablas"""
    print("🗑️  Eliminando todas las tablas existentes...")

    # Eliminar tablas en orden inverso a las dependencias
    try:
        Documento.__table__.drop(engine, checkfirst=True)
        Carpeta.__table__.drop(engine, checkfirst=True)
        PagoSocio.__table__.drop(engine, checkfirst=True)
        Pago.__table__.drop(engine, checkfirst=True)
        Prestamo.__table__.drop(engine, checkfirst=True)
        Socio.__table__.drop(engine, checkfirst=True)
        Cliente.__table__.drop(engine, checkfirst=True)
        Usuario.__table__.drop(engine, checkfirst=True)
        Rol.__table__.drop(engine, checkfirst=True)
        Configuracion.__table__.drop(engine, checkfirst=True)
        print("✅ Tablas eliminadas correctamente")
    except Exception as e:
        print(f"⚠️  Error eliminando tablas (posiblemente ya no existían): {e}")

    # Recrear todas las tablas
    print("🔨 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Todas las tablas creadas correctamente")

def create_roles(db):
    print("👥 Creando roles...")
    roles_data = [
        {"nombre": "admin", "descripcion": "Administrador del sistema"},
        {"nombre": "digitador", "descripcion": "Digitador de datos"}
    ]

    for rol_data in roles_data:
        rol = Rol(**rol_data)
        db.add(rol)

    db.commit()
    print("✅ Roles creados correctamente")
    return db.query(Rol).all()

def create_users(db, roles):
    print("👤 Creando usuarios...")
    admin_role = next(r for r in roles if r.nombre == "admin")
    digitador_role = next(r for r in roles if r.nombre == "digitador")

    users_data = [
        {
            "nombre_completo": "Administrador Sistema",
            "username": "admin",
            "email": "admin@sistema.com",
            "hashed_password": get_password_hash("admin123"),
            "rol_id": admin_role.id,
            "activo": True
        },
        {
            "nombre_completo": "Digitador Uno",
            "username": "digitador1",
            "email": "digitador1@sistema.com",
            "hashed_password": get_password_hash("digi123"),
            "rol_id": digitador_role.id,
            "activo": True
        }
    ]

    for user_data in users_data:
        user = Usuario(**user_data)
        db.add(user)

    db.commit()
    print("✅ Usuarios creados correctamente")
    return db.query(Usuario).all()

def create_clientes(db):
    print("👨‍👩‍👧‍👦 Creando clientes...")
    clientes_data = [
        {
            "cedula": "12345678",
            "nombre_completo": "Ana María López García",
            "fecha_nacimiento": date(1985, 3, 15),
            "telefono": "+57 300 123 4567",
            "email": "ana.lopez@email.com",
            "direccion": "Calle 123 #45-67, Bogotá",
            "ocupacion": "Profesora",
            "ingresos_mensuales": 2500000,
            "referencias_personales": "Juan Pérez - Amigo",
            "activo": True
        },
        {
            "cedula": "87654321",
            "nombre_completo": "Juan Carlos Martínez Rodríguez",
            "fecha_nacimiento": date(1990, 7, 22),
            "telefono": "+57 301 987 6543",
            "email": "juan.martinez@email.com",
            "direccion": "Carrera 89 #12-34, Medellín",
            "ocupacion": "Ingeniero",
            "ingresos_mensuales": 3500000,
            "referencias_personales": "María González - Colega",
            "activo": True
        }
    ]

    for cliente_data in clientes_data:
        cliente = Cliente(**cliente_data)
        db.add(cliente)

    db.commit()
    print("✅ Clientes creados correctamente")
    return db.query(Cliente).all()

def create_socios(db):
    print("🤝 Creando socios...")
    socios_data = [
        {
            "cedula": "11111111",
            "nombre_completo": "María González López",
            "telefono": "+57 302 111 2222",
            "email": "maria.gonzalez@email.com",
            "direccion": "Avenida 68 #34-56, Bogotá",
            "fecha_nacimiento": date(1975, 12, 10),
            "ocupacion": "Empresaria",
            "ingresos_mensuales": 8000000,
            "referencias_personales": "Carlos Rodríguez - Socio",
            "activo": True,
            "capital_inicial": Decimal("50000000"),
            "capital_actual": Decimal("46580350"),
            "porcentaje_participacion": Decimal("60.0")
        },
        {
            "cedula": "22222222",
            "nombre_completo": "Carlos Rodríguez Pérez",
            "telefono": "+57 303 333 4444",
            "email": "carlos.rodriguez@email.com",
            "direccion": "Calle 72 #89-01, Bogotá",
            "fecha_nacimiento": date(1980, 5, 18),
            "ocupacion": "Inversionista",
            "ingresos_mensuales": 6000000,
            "referencias_personales": "Luis Mendoza - Amigo",
            "activo": True,
            "capital_inicial": Decimal("30000000"),
            "capital_actual": Decimal("30000000"),
            "porcentaje_participacion": Decimal("40.0")
        }
    ]

    for socio_data in socios_data:
        socio = Socio(**socio_data)
        db.add(socio)

    db.commit()
    print("✅ Socios creados correctamente")
    return db.query(Socio).all()

def create_pagos_socios(db, socios, admin_user):
    """Crear pagos/movimientos de socios con datos que generen cálculos correctos"""
    print("💰 Creando movimientos de socios...")

    pagos_creados = 0

    for socio in socios:
        # Crear aportes iniciales
        aporte_inicial = PagoSocio(
            socio_id=socio.id,
            tipo="aporte",
            monto=socio.capital_inicial,
            fecha_pago=socio.creado_en.date() if socio.creado_en else date.today() - timedelta(days=365),
            metodo_pago="transferencia",
            descripcion=f"Aporte inicial de capital: ${socio.capital_inicial:,.0f}",
            registrado_por=admin_user.id
        )
        aporte_inicial.saldo_anterior = 0
        aporte_inicial.saldo_nuevo = float(socio.capital_inicial)
        db.add(aporte_inicial)
        pagos_creados += 1

        # Crear algunas ganancias (retiros)
        num_ganancias = random.randint(2, 4)
        fecha_base = socio.creado_en.date() if socio.creado_en else date.today() - timedelta(days=300)

        for i in range(num_ganancias):
            fecha_ganancia = fecha_base + timedelta(days=random.randint(60, 300))
            monto_ganancia = Decimal(str(random.randint(500000, 1500000)))

            ganancia = PagoSocio(
                socio_id=socio.id,
                tipo="ganancia",
                monto=monto_ganancia,
                fecha_pago=fecha_ganancia,
                metodo_pago="transferencia",
                descripcion=f"Distribución de ganancias del período {fecha_ganancia.strftime('%m/%Y')}",
                registrado_por=admin_user.id
            )

            # Calcular saldos
            socio_actual = db.query(Socio).filter(Socio.id == socio.id).first()
            ganancia.saldo_anterior = socio_actual.capital_actual
            ganancia.saldo_nuevo = float(socio_actual.capital_actual) - float(monto_ganancia)

            db.add(ganancia)
            pagos_creados += 1

            # Actualizar capital del socio
            socio_actual.capital_actual = ganancia.saldo_nuevo

    db.commit()
    print(f"✅ {pagos_creados} movimientos de socios creados correctamente")

def create_prestamos_completos(db, clientes, socios, admin_user):
    """Crear préstamos completos con pagos para testing exhaustivo"""
    print("💰 Creando préstamos completos con pagos...")

    prestamos_creados = 0
    pagos_creados = 0
    fecha_base = date.today() - timedelta(days=120)

    # Préstamo 1: Cliente Ana María, empresa
    prestamo1 = Prestamo(
        cliente_id=clientes[0].id,
        monto=Decimal("12000000"),
        tasa_interes=2.5,
        plazo_meses=24,
        fecha_inicio=fecha_base,
        origen="empresa",
        observaciones="Préstamo para educación superior"
    )
    prestamo1.numero_cuotas = 24
    prestamo1.valor_cuota = prestamo1.calcular_cuota()
    prestamo1.total_intereses = (prestamo1.valor_cuota * 24) - float(prestamo1.monto)
    prestamo1.total_pagar = prestamo1.valor_cuota * 24
    prestamo1.saldo_pendiente = prestamo1.total_pagar
    db.add(prestamo1)
    db.flush()  # Para obtener el ID
    prestamos_creados += 1

    # Crear pagos para préstamo 1 (15 pagos)
    fecha_pago = prestamo1.fecha_inicio
    for i in range(1, 16):
        fecha_pago = fecha_pago + timedelta(days=30)
        if fecha_pago > date.today():
            break

        pago = Pago(
            prestamo_id=prestamo1.id,
            numero_cuota=i,
            fecha_pago=fecha_pago,
            monto_pagado=prestamo1.valor_cuota,
            tipo_pago="cuota",
            metodo_pago="transferencia",
            referencia_pago=f"REC-{prestamo1.id}-{i:03d}",
            observaciones=f"Pago cuota {i} del préstamo"
        )
        pago.capital_pagado = round(float(prestamo1.valor_cuota) * 0.7, 2)
        pago.intereses_pagados = round(float(prestamo1.valor_cuota) * 0.3, 2)

        db.add(pago)
        pagos_creados += 1

        prestamo1.cuotas_pagadas += 1
        prestamo1.saldo_pendiente -= pago.monto_pagado

    # Préstamo 2: Cliente Juan Carlos, socio María González
    prestamo2 = Prestamo(
        cliente_id=clientes[1].id,
        socio_id=socios[0].id,
        monto=Decimal("18000000"),
        tasa_interes=2.8,
        plazo_meses=36,
        fecha_inicio=fecha_base + timedelta(days=15),
        origen="socio",
        observaciones="Préstamo para emprendimiento"
    )
    prestamo2.numero_cuotas = 36
    prestamo2.valor_cuota = prestamo2.calcular_cuota()
    prestamo2.total_intereses = (prestamo2.valor_cuota * 36) - float(prestamo2.monto)
    prestamo2.total_pagar = prestamo2.valor_cuota * 36
    prestamo2.saldo_pendiente = prestamo2.total_pagar
    db.add(prestamo2)
    db.flush()
    prestamos_creados += 1

    # Registrar préstamo en movimientos de socio
    socio = socios[0]
    saldo_anterior = socio.capital_actual
    socio.capital_actual = float(socio.capital_actual) - float(prestamo2.monto)
    saldo_nuevo = socio.capital_actual

    pago_socio_prestamo = PagoSocio(
        socio_id=socio.id,
        tipo="prestamo",
        monto=prestamo2.monto,
        fecha_pago=prestamo2.fecha_inicio,
        descripcion=f"Préstamo #{prestamo2.id} al cliente {clientes[1].nombre_completo}",
        prestamo_id=prestamo2.id,
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        registrado_por=admin_user.id
    )
    db.add(pago_socio_prestamo)
    db.add(socio)

    # Crear pagos para préstamo 2 (20 pagos) y generar devoluciones
    fecha_pago = prestamo2.fecha_inicio
    for i in range(1, 21):
        fecha_pago = fecha_pago + timedelta(days=30)
        if fecha_pago > date.today():
            break

        pago = Pago(
            prestamo_id=prestamo2.id,
            numero_cuota=i,
            fecha_pago=fecha_pago,
            monto_pagado=prestamo2.valor_cuota,
            tipo_pago="cuota",
            metodo_pago="efectivo",
            referencia_pago=f"REC-{prestamo2.id}-{i:03d}",
            observaciones=f"Pago cuota {i} del préstamo con socio"
        )
        pago.capital_pagado = round(float(prestamo2.valor_cuota) * 0.7, 2)
        pago.intereses_pagados = round(float(prestamo2.valor_cuota) * 0.3, 2)

        db.add(pago)
        pagos_creados += 1

        prestamo2.cuotas_pagadas += 1
        prestamo2.saldo_pendiente -= pago.monto_pagado

        # Generar devolución automática al socio
        monto_devolucion = round(float(pago.capital_pagado) * 0.7, 2)  # 70% del capital
        if monto_devolucion > 0:
            saldo_anterior_dev = socio.capital_actual
            socio.capital_actual = float(socio.capital_actual) + float(monto_devolucion)
            saldo_nuevo_dev = socio.capital_actual

            pago_devolucion = PagoSocio(
                socio_id=socio.id,
                tipo="devolucion",
                monto=monto_devolucion,
                fecha_pago=fecha_pago,
                descripcion=f"Devolución cuota #{i} del préstamo #{prestamo2.id}",
                prestamo_id=prestamo2.id,
                saldo_anterior=saldo_anterior_dev,
                saldo_nuevo=saldo_nuevo_dev,
                registrado_por=admin_user.id
            )
            db.add(pago_devolucion)
            db.add(socio)

    db.commit()
    print(f"✅ {prestamos_creados} préstamos completos creados correctamente")
    print(f"✅ {pagos_creados} pagos de préstamos creados correctamente")

def main():
    print("🚀 Iniciando reset completo de base de datos...")

    # Reset database
    reset_database()

    db = SessionLocal()

    try:
        # Create basic data
        roles = create_roles(db)
        users = create_users(db, roles)
        admin_user = next(u for u in users if u.username == "admin")

        clientes = create_clientes(db)
        socios = create_socios(db)

        # Create socio payments
        create_pagos_socios(db, socios, admin_user)

        # Create complete loans with payments
        create_prestamos_completos(db, clientes, socios, admin_user)

        print("\n✅ Base de datos COMPLETA reseteada y poblada correctamente!")
        print("\nDatos creados:")
        print(f"- Roles: {len(roles)}")
        print(f"- Usuarios: {len(users)}")
        print(f"- Clientes: {len(clientes)}")
        print(f"- Socios: {len(socios)}")

        # Verificar datos
        total_prestamos = db.query(Prestamo).count()
        total_pagos = db.query(Pago).count()
        total_pagos_socio = db.query(PagoSocio).count()
        print(f"- Préstamos: {total_prestamos}")
        print(f"- Pagos de préstamos: {total_pagos}")
        print(f"- Movimientos de socios: {total_pagos_socio}")

        # Mostrar estadísticas calculadas para verificar
        print("\n📊 Estadísticas finales de socios:")
        for socio in socios:
            aportes = db.query(PagoSocio.monto).filter(
                PagoSocio.socio_id == socio.id,
                PagoSocio.tipo == "aporte"
            ).all()
            total_aportes = sum(float(a[0]) for a in aportes)

            prestamos_socio = db.query(PagoSocio.monto).filter(
                PagoSocio.socio_id == socio.id,
                PagoSocio.tipo == "prestamo"
            ).all()
            total_prestamos_socio = sum(float(p[0]) for p in prestamos_socio)

            devoluciones = db.query(PagoSocio.monto).filter(
                PagoSocio.socio_id == socio.id,
                PagoSocio.tipo == "devolucion"
            ).all()
            total_devoluciones = sum(float(d[0]) for d in devoluciones)

            ganancias = db.query(PagoSocio.monto).filter(
                PagoSocio.socio_id == socio.id,
                PagoSocio.tipo == "ganancia"
            ).all()
            total_ganancias = sum(float(g[0]) for g in ganancias)

            print(f"\n{socio.nombre_completo}:")
            print(f"  - Aportes: ${total_aportes:,.2f}")
            print(f"  - Préstamos realizados: ${total_prestamos_socio:,.2f}")
            print(f"  - Devoluciones recibidas: ${total_devoluciones:,.2f}")
            print(f"  - Ganancias distribuidas: ${total_ganancias:,.2f}")
            print(f"  - Capital actual: ${socio.capital_actual:,.2f}")

        print("\n🎯 Base de datos lista para testing completo!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
