#!/usr/bin/env python3
"""
Script completo para resetear la base de datos con datos exhaustivos de prueba
Incluye: clientes, socios, préstamos, pagos, movimientos de socios, etc.
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

from app.core.security import get_password_hash

def reset_database():
    """Vacía completamente la base de datos y recrea todas las tablas"""
    print("🗑️  Eliminando todas las tablas existentes...")

    try:
        Pago.__table__.drop(engine, checkfirst=True)
        Prestamo.__table__.drop(engine, checkfirst=True)
        PagoSocio.__table__.drop(engine, checkfirst=True)
        Socio.__table__.drop(engine, checkfirst=True)
        Cliente.__table__.drop(engine, checkfirst=True)
        Usuario.__table__.drop(engine, checkfirst=True)
        Rol.__table__.drop(engine, checkfirst=True)
        Configuracion.__table__.drop(engine, checkfirst=True)
        print("✅ Tablas eliminadas correctamente")
    except Exception as e:
        print(f"⚠️  Error eliminando tablas: {e}")

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
        },
        {
            "cedula": "11223344",
            "nombre_completo": "María Fernanda García López",
            "fecha_nacimiento": date(1988, 11, 5),
            "telefono": "+57 302 555 1234",
            "email": "maria.garcia@email.com",
            "direccion": "Avenida 68 #45-23, Cali",
            "ocupacion": "Contadora",
            "ingresos_mensuales": 2800000,
            "referencias_personales": "Carlos Rodríguez - Familiar",
            "activo": True
        },
        {
            "cedula": "44332211",
            "nombre_completo": "Carlos Andrés Pérez Sánchez",
            "fecha_nacimiento": date(1982, 1, 30),
            "telefono": "+57 303 777 8901",
            "email": "carlos.perez@email.com",
            "direccion": "Calle 72 #89-45, Barranquilla",
            "ocupacion": "Abogado",
            "ingresos_mensuales": 4200000,
            "referencias_personales": "Ana López - Compañero de trabajo",
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

def create_prestamos(db, clientes, socios, admin_user):
    print("💰 Creando préstamos...")

    prestamos_creados = 0
    fecha_base = date.today() - timedelta(days=180)  # 6 meses atrás

    # Préstamo 1: Cliente Ana María, empresa (sin socio)
    prestamo1 = Prestamo(
        cliente_id=clientes[0].id,
        monto=Decimal("10000000"),  # 10 millones
        tasa_interes=2.5,
        plazo_meses=24,
        fecha_inicio=fecha_base,
        origen="empresa",
        observaciones="Préstamo personal para educación"
    )
    prestamo1.numero_cuotas = 24
    prestamo1.valor_cuota = prestamo1.calcular_cuota()
    prestamo1.total_intereses = (prestamo1.valor_cuota * 24) - float(prestamo1.monto)
    prestamo1.total_pagar = prestamo1.valor_cuota * 24
    prestamo1.saldo_pendiente = prestamo1.total_pagar
    db.add(prestamo1)
    prestamos_creados += 1

    # Préstamo 2: Cliente Juan Carlos, socio María González
    prestamo2 = Prestamo(
        cliente_id=clientes[1].id,
        socio_id=socios[0].id,  # María González
        monto=Decimal("15000000"),  # 15 millones
        tasa_interes=2.8,
        plazo_meses=36,
        fecha_inicio=fecha_base + timedelta(days=30),
        origen="socio",
        observaciones="Préstamo para negocio familiar"
    )
    prestamo2.numero_cuotas = 36
    prestamo2.valor_cuota = prestamo2.calcular_cuota()
    prestamo2.total_intereses = (prestamo2.valor_cuota * 36) - float(prestamo2.monto)
    prestamo2.total_pagar = prestamo2.valor_cuota * 36
    prestamo2.saldo_pendiente = prestamo2.total_pagar
    db.add(prestamo2)

    # Registrar movimiento de socio (préstamo)
    socio = socios[0]
    saldo_anterior = socio.capital_actual
    socio.capital_actual = float(socio.capital_actual) - float(prestamo2.monto)
    saldo_nuevo = socio.capital_actual

    pago_socio_prestamo = PagoSocio(
        socio_id=socio.id,
        tipo="prestamo",
        monto=prestamo2.monto,
        fecha_pago=prestamo2.fecha_inicio,
        descripcion=f"Préstamo #{prestamo2.id} al cliente",
        prestamo_id=prestamo2.id,
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        registrado_por=admin_user.id
    )
    db.add(pago_socio_prestamo)
    db.add(socio)
    prestamos_creados += 1

    # Préstamo 3: Cliente María Fernanda, empresa
    prestamo3 = Prestamo(
        cliente_id=clientes[2].id,
        monto=Decimal("8000000"),  # 8 millones
        tasa_interes=2.2,
        plazo_meses=18,
        fecha_inicio=fecha_base + timedelta(days=60),
        origen="empresa",
        observaciones="Préstamo para vivienda"
    )
    prestamo3.numero_cuotas = 18
    prestamo3.valor_cuota = prestamo3.calcular_cuota()
    prestamo3.total_intereses = (prestamo3.valor_cuota * 18) - float(prestamo3.monto)
    prestamo3.total_pagar = prestamo3.valor_cuota * 18
    prestamo3.saldo_pendiente = prestamo3.total_pagar
    db.add(prestamo3)
    prestamos_creados += 1

    # Préstamo 4: Cliente Carlos Andrés, socio Carlos Rodríguez (activo)
    prestamo4 = Prestamo(
        cliente_id=clientes[3].id,
        socio_id=socios[1].id,  # Carlos Rodríguez
        monto=Decimal("20000000"),  # 20 millones
        tasa_interes=3.0,
        plazo_meses=48,
        fecha_inicio=fecha_base + timedelta(days=90),
        origen="socio",
        observaciones="Préstamo para expansión de negocio"
    )
    prestamo4.numero_cuotas = 48
    prestamo4.valor_cuota = prestamo4.calcular_cuota()
    prestamo4.total_intereses = (prestamo4.valor_cuota * 48) - float(prestamo4.monto)
    prestamo4.total_pagar = prestamo4.valor_cuota * 48
    prestamo4.saldo_pendiente = prestamo4.total_pagar
    db.add(prestamo4)

    # Registrar movimiento de socio (préstamo)
    socio = socios[1]
    saldo_anterior = socio.capital_actual
    socio.capital_actual = float(socio.capital_actual) - float(prestamo4.monto)
    saldo_nuevo = socio.capital_actual

    pago_socio_prestamo2 = PagoSocio(
        socio_id=socio.id,
        tipo="prestamo",
        monto=prestamo4.monto,
        fecha_pago=prestamo4.fecha_inicio,
        descripcion=f"Préstamo #{prestamo4.id} al cliente",
        prestamo_id=prestamo4.id,
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        registrado_por=admin_user.id
    )
    db.add(pago_socio_prestamo2)
    db.add(socio)
    prestamos_creados += 1

    db.commit()
    print(f"✅ {prestamos_creados} préstamos creados correctamente")
    return db.query(Prestamo).all()

def create_pagos(db, prestamos, admin_user):
    print("💳 Creando pagos de préstamos...")

    pagos_creados = 0
    fecha_actual = date.today()

    for prestamo in prestamos:
        if prestamo.origen == "empresa":
            # Para préstamos de empresa, crear algunos pagos
            num_pagos = random.randint(3, prestamo.numero_cuotas - 2)
        else:
            # Para préstamos de socio, crear más pagos para generar devoluciones
            num_pagos = random.randint(6, prestamo.numero_cuotas - 1)

        fecha_pago = prestamo.fecha_inicio

        for cuota_num in range(1, num_pagos + 1):
            # Simular algunos pagos atrasados
            if cuota_num in [2, 5, 8]:
                fecha_pago = fecha_pago + timedelta(days=random.randint(35, 45))
            else:
                fecha_pago = fecha_pago + timedelta(days=30)

            # Evitar fechas futuras
            if fecha_pago > fecha_actual:
                fecha_pago = fecha_actual - timedelta(days=random.randint(1, 30))

            # Crear pago
            pago = Pago(
                prestamo_id=prestamo.id,
                numero_cuota=cuota_num,
                fecha_pago=fecha_pago,
                monto_pagado=prestamo.valor_cuota,
                tipo_pago="cuota",
                metodo_pago=random.choice(["efectivo", "transferencia", "cheque"]),
                referencia_pago=f"REC-{prestamo.id}-{cuota_num:03d}",
                observaciones=f"Pago cuota {cuota_num}"
            )

            # Calcular desglose
            pago.capital_pagado = round(float(prestamo.valor_cuota) * 0.7, 2)
            pago.intereses_pagados = round(float(prestamo.valor_cuota) * 0.3, 2)

            db.add(pago)
            pagos_creados += 1

            # Actualizar préstamo
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= pago.monto_pagado

            # Si es préstamo de socio, generar devolución automática
            if prestamo.origen == "socio" and prestamo.socio_id:
                socio = db.query(Socio).filter(Socio.id == prestamo.socio_id).first()
                if socio:
                    # Calcular devolución proporcional (70% del capital pagado)
                    monto_devolucion = round(float(pago.capital_pagado) * 0.7, 2)

                    if monto_devolucion > 0:
                        saldo_anterior = socio.capital_actual
                        socio.capital_actual = float(socio.capital_actual) + float(monto_devolucion)
                        saldo_nuevo = socio.capital_actual

                        pago_devolucion = PagoSocio(
                            socio_id=socio.id,
                            tipo="devolucion",
                            monto=monto_devolucion,
                            fecha_pago=fecha_pago,
                            descripcion=f"Cuota #{cuota_num} del préstamo #{prestamo.id}",
                            prestamo_id=prestamo.id,
                            saldo_anterior=saldo_anterior,
                            saldo_nuevo=saldo_nuevo,
                            registrado_por=admin_user.id
                        )
                        db.add(pago_devolucion)
                        db.add(socio)

            # Verificar si préstamo está pagado
            if prestamo.saldo_pendiente <= 0:
                prestamo.estado = "pagado"
                prestamo.saldo_pendiente = 0

    db.commit()
    print(f"✅ {pagos_creados} pagos de préstamos creados correctamente")

def create_pagos_socios(db, socios, admin_user):
    """Crear aportes iniciales y algunas ganancias para socios"""
    print("💰 Creando movimientos iniciales de socios...")

    pagos_creados = 0

    for socio in socios:
        # Aporte inicial (ya debería estar creado, pero aseguramos)
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

        # Algunas ganancias históricas
        num_ganancias = random.randint(2, 4)
        fecha_base = socio.creado_en.date() if socio.creado_en else date.today() - timedelta(days=300)

        for i in range(num_ganancias):
            fecha_ganancia = fecha_base + timedelta(days=random.randint(60, 300))
            monto_ganancia = Decimal(str(random.randint(400000, 1200000)))

            # Evitar fechas futuras
            if fecha_ganancia > date.today():
                fecha_ganancia = date.today() - timedelta(days=random.randint(30, 90))

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
    print(f"✅ {pagos_creados} movimientos iniciales de socios creados correctamente")

def main():
    print("🚀 Iniciando reset completo de base de datos con datos exhaustivos...")

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

        # Create socio payments (initial)
        create_pagos_socios(db, socios, admin_user)

        # Create loans
        prestamos = create_prestamos(db, clientes, socios, admin_user)

        # Create payments (this will also create socio returns)
        create_pagos(db, prestamos, admin_user)

        print("\n✅ Base de datos COMPLETA reseteada y poblada correctamente!")
        print("\nDatos creados:")
        print(f"- Roles: {len(roles)}")
        print(f"- Usuarios: {len(users)}")
        print(f"- Clientes: {len(clientes)}")
        print(f"- Socios: {len(socios)}")
        print(f"- Préstamos: {len(prestamos)}")

        # Contar pagos
        total_pagos = db.query(Pago).count()
        total_pagos_socio = db.query(PagoSocio).count()
        print(f"- Pagos de préstamos: {total_pagos}")
        print(f"- Movimientos de socios: {total_pagos_socio}")

        # Mostrar estadísticas finales
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
