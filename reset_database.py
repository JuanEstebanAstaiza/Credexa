#!/usr/bin/env python3
"""
Script para resetear completamente la base de datos y llenarla con datos sintéticos
para probar todas las funcionalidades del sistema de gestión de préstamos.
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

    # Eliminar tablas en orden inverso a las dependencias
    try:
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
    """Crear roles básicos del sistema"""
    print("👥 Creando roles del sistema...")

    roles = [
        {"id": 1, "nombre": "admin", "descripcion": "Administrador del sistema", "activo": True},
        {"id": 2, "nombre": "digitador", "descripcion": "Usuario con permisos limitados", "activo": True},
    ]

    for rol_data in roles:
        rol = Rol(**rol_data)
        db.add(rol)

    db.commit()
    print("✅ Roles creados correctamente")

def create_users(db):
    """Crear usuarios de prueba"""
    print("👤 Creando usuarios de prueba...")

    users = [
        {
            "username": "admin",
            "nombre_completo": "Administrador del Sistema",
            "email": "admin@gestionprestamos.com",
            "hashed_password": get_password_hash("admin123"),
            "activo": True,
            "rol_id": 1
        },
        {
            "username": "digitador",
            "nombre_completo": "Usuario Digitador",
            "email": "digitador@gestionprestamos.com",
            "hashed_password": get_password_hash("digitador123"),
            "activo": True,
            "rol_id": 2
        },
    ]

    for user_data in users:
        user = Usuario(**user_data)
        db.add(user)

    db.commit()
    print("✅ Usuarios creados correctamente")

def create_configurations(db):
    """Crear configuraciones básicas del sistema"""
    print("⚙️  Creando configuraciones del sistema...")

    configs = [
        {
            "clave": "empresa_nombre",
            "valor": "Credexa - Gestión de Préstamos",
            "tipo": "string",
            "categoria": "empresa",
            "descripcion": "Nombre de la empresa"
        },
        {
            "clave": "empresa_nit",
            "valor": "901234567-1",
            "tipo": "string",
            "categoria": "empresa",
            "descripcion": "NIT de la empresa"
        },
        {
            "clave": "tasa_interes_default",
            "valor": "2.5",
            "tipo": "decimal",
            "categoria": "financiero",
            "descripcion": "Tasa de interés mensual por defecto"
        },
        {
            "clave": "plazo_maximo_meses",
            "valor": "360",
            "tipo": "integer",
            "categoria": "financiero",
            "descripcion": "Plazo máximo en meses"
        },
    ]

    for config_data in configs:
        config = Configuracion(**config_data)
        db.add(config)

    db.commit()
    print("✅ Configuraciones creadas correctamente")

def create_clientes(db):
    """Crear clientes de prueba"""
    print("👥 Creando clientes de prueba...")

    # Datos realistas de clientes colombianos
    clientes_data = [
        {
            "cedula": "1012345678",
            "nombre_completo": "Ana María López García",
            "telefono": "3001234567",
            "email": "ana.lopez@email.com",
            "direccion": "Calle 123 #45-67, Bogotá",
            "fecha_nacimiento": date(1985, 3, 15),
            "ocupacion": "Profesora",
            "ingresos_mensuales": 2500000,
            "activo": True
        },
        {
            "cedula": "1023456789",
            "nombre_completo": "Juan Carlos Martínez Rodríguez",
            "telefono": "3012345678",
            "email": "juan.martinez@email.com",
            "direccion": "Carrera 78 #12-34, Medellín",
            "fecha_nacimiento": date(1978, 7, 22),
            "ocupacion": "Ingeniero Civil",
            "ingresos_mensuales": 4500000,
            "activo": True
        },
        {
            "cedula": "1034567890",
            "nombre_completo": "María Fernanda González Pérez",
            "telefono": "3023456789",
            "email": "maria.gonzalez@email.com",
            "direccion": "Avenida 68 #45-12, Cali",
            "fecha_nacimiento": date(1990, 11, 8),
            "ocupacion": "Médica",
            "ingresos_mensuales": 5500000,
            "activo": True
        },
        {
            "cedula": "1045678901",
            "nombre_completo": "Carlos Alberto Ramírez Soto",
            "telefono": "3034567890",
            "email": "carlos.ramirez@email.com",
            "direccion": "Diagonal 45 #23-56, Barranquilla",
            "fecha_nacimiento": date(1982, 5, 30),
            "ocupacion": "Abogado",
            "ingresos_mensuales": 3800000,
            "activo": True
        },
        {
            "cedula": "1056789012",
            "nombre_completo": "Laura Patricia Torres Muñoz",
            "telefono": "3045678901",
            "email": "laura.torres@email.com",
            "direccion": "Transversal 18 #67-89, Cartagena",
            "fecha_nacimiento": date(1988, 9, 14),
            "ocupacion": "Contadora",
            "ingresos_mensuales": 3200000,
            "activo": True
        },
        {
            "cedula": "1067890123",
            "nombre_completo": "Diego Alejandro Morales Castro",
            "telefono": "3056789012",
            "email": "diego.morales@email.com",
            "direccion": "Calle 72 #8-45, Bucaramanga",
            "fecha_nacimiento": date(1975, 12, 3),
            "ocupacion": "Empresario",
            "ingresos_mensuales": 8000000,
            "activo": True
        },
        {
            "cedula": "1078901234",
            "nombre_completo": "Sofia Isabel Vargas Ruiz",
            "telefono": "3067890123",
            "email": "sofia.vargas@email.com",
            "direccion": "Carrera 15 #89-01, Pereira",
            "fecha_nacimiento": date(1992, 1, 25),
            "ocupacion": "Arquitecta",
            "ingresos_mensuales": 4200000,
            "activo": True
        },
        {
            "cedula": "1089012345",
            "nombre_completo": "Andrés Felipe Sánchez Gómez",
            "telefono": "3078901234",
            "email": "andres.sanchez@email.com",
            "direccion": "Avenida Circunvalar #123-45, Manizales",
            "fecha_nacimiento": date(1980, 6, 18),
            "ocupacion": "Dentista",
            "ingresos_mensuales": 4800000,
            "activo": True
        },
    ]

    clientes = []
    for cliente_data in clientes_data:
        cliente = Cliente(**cliente_data)
        db.add(cliente)
        clientes.append(cliente)

    db.commit()
    print(f"✅ {len(clientes)} clientes creados correctamente")
    return clientes

def create_socios(db):
    """Crear socios de prueba"""
    print("🤝 Creando socios de prueba...")

    # Datos de socios con cédulas que coinciden con usuarios creados
    socios_data = [
        {
            "nombre_completo": "María González López",
            "cedula": "12345678",  # Coincide con usuario
            "telefono": "3101234567",
            "email": "maria.gonzalez@email.com",
            "direccion": "Carrera 7 #23-45, Bogotá",
            "fecha_nacimiento": date(1970, 4, 10),
            "ocupacion": "Empresaria",
            "ingresos_mensuales": 12000000,
            "referencias_personales": "Banco de Bogotá - Gerente: Ana López (3001112222)",
            "activo": True,
            "notas": "Socia fundadora con amplia experiencia en finanzas",
            "capital_inicial": Decimal("50000000"),  # 50 millones iniciales
            "capital_actual": Decimal("55000000"),  # 55 millones actuales (ganancias)
            "porcentaje_participacion": Decimal("25.0")  # 25% de participación
        },
        {
            "nombre_completo": "Carlos Rodríguez Pérez",
            "cedula": "87654321",  # Coincide con usuario
            "telefono": "3112345678",
            "email": "carlos.rodriguez@email.com",
            "direccion": "Avenida Chile #45-67, Medellín",
            "fecha_nacimiento": date(1965, 8, 22),
            "ocupacion": "Inversionista",
            "ingresos_mensuales": 18000000,
            "referencias_personales": "BBVA - Director: Pedro Rodríguez (3012223333)",
            "activo": True,
            "notas": "Socio inversionista con background en banca",
            "capital_inicial": Decimal("80000000"),  # 80 millones iniciales
            "capital_actual": Decimal("87500000"),  # 87.5 millones actuales
            "porcentaje_participacion": Decimal("35.0")  # 35% de participación
        },
        {
            "nombre_completo": "Luis Alberto Mendoza Silva",
            "cedula": "11223344",
            "telefono": "3123456789",
            "email": "luis.mendoza@email.com",
            "direccion": "Calle 5 #12-34, Cali",
            "fecha_nacimiento": date(1978, 12, 5),
            "ocupacion": "Comerciante",
            "ingresos_mensuales": 9500000,
            "referencias_personales": "Cámara de Comercio - Presidente: María Silva (3023334444)",
            "activo": True,
            "notas": "Socio con experiencia en sector comercial",
            "capital_inicial": Decimal("30000000"),  # 30 millones iniciales
            "capital_actual": Decimal("32000000"),  # 32 millones actuales
            "porcentaje_participacion": Decimal("20.0")  # 20% de participación
        },
    ]

    socios = []
    for socio_data in socios_data:
        socio = Socio(**socio_data)
        db.add(socio)
        socios.append(socio)

    db.commit()
    print(f"✅ {len(socios)} socios creados correctamente")
    return socios

def create_prestamos(db, clientes, socios):
    """Crear préstamos de prueba (de empresa y de socios)"""
    print("💰 Creando préstamos de prueba...")

    # Obtener usuario admin para registrar pagos
    admin_user = db.query(Usuario).filter(Usuario.username == "admin").first()

    prestamos_data = [
        # Préstamos de EMPRESA (origen = "empresa")
        {
            "cliente_id": clientes[0].id,  # Ana López
            "monto": Decimal("5000000"),  # 5 millones
            "tasa_interes": Decimal("2.5"),
            "plazo_meses": 24,
            "fecha_inicio": date.today() - timedelta(days=180),  # 6 meses atrás
            "origen": "empresa",
            "socio_id": None,
            "observaciones": "Préstamo para educación superior"
        },
        {
            "cliente_id": clientes[1].id,  # Juan Martínez
            "monto": Decimal("8000000"),  # 8 millones
            "tasa_interes": Decimal("2.3"),
            "plazo_meses": 36,
            "fecha_inicio": date.today() - timedelta(days=120),  # 4 meses atrás
            "origen": "empresa",
            "socio_id": None,
            "observaciones": "Préstamo para vivienda"
        },
        {
            "cliente_id": clientes[2].id,  # María González
            "monto": Decimal("3000000"),  # 3 millones
            "tasa_interes": Decimal("2.8"),
            "plazo_meses": 18,
            "fecha_inicio": date.today() - timedelta(days=90),  # 3 meses atrás
            "origen": "empresa",
            "socio_id": None,
            "observaciones": "Préstamo personal"
        },
        # Préstamos de SOCIOS (origen = "socio")
        {
            "cliente_id": clientes[3].id,  # Carlos Ramírez
            "monto": Decimal("4000000"),  # 4 millones
            "tasa_interes": Decimal("2.2"),
            "plazo_meses": 20,
            "fecha_inicio": date.today() - timedelta(days=60),  # 2 meses atrás
            "origen": "socio",
            "socio_id": socios[0].id,  # María González
            "observaciones": "Préstamo financiado por socia María González"
        },
        {
            "cliente_id": clientes[4].id,  # Laura Torres
            "monto": Decimal("6000000"),  # 6 millones
            "tasa_interes": Decimal("2.1"),
            "plazo_meses": 30,
            "fecha_inicio": date.today() - timedelta(days=45),  # 1.5 meses atrás
            "origen": "socio",
            "socio_id": socios[1].id,  # Carlos Rodríguez
            "observaciones": "Préstamo financiado por socio Carlos Rodríguez"
        },
        {
            "cliente_id": clientes[5].id,  # Diego Morales
            "monto": Decimal("2500000"),  # 2.5 millones
            "tasa_interes": Decimal("2.4"),
            "plazo_meses": 15,
            "fecha_inicio": date.today() - timedelta(days=30),  # 1 mes atrás
            "origen": "socio",
            "socio_id": socios[2].id,  # Luis Mendoza
            "observaciones": "Préstamo financiado por socio Luis Mendoza"
        },
        # Préstamos PAGADOS (para mostrar historial)
        {
            "cliente_id": clientes[6].id,  # Sofía Vargas
            "monto": Decimal("2000000"),  # 2 millones
            "tasa_interes": Decimal("2.6"),
            "plazo_meses": 12,
            "fecha_inicio": date.today() - timedelta(days=400),  # 13 meses atrás
            "origen": "empresa",
            "socio_id": None,
            "estado": "pagado",
            "observaciones": "Préstamo pagado completamente"
        },
        {
            "cliente_id": clientes[7].id,  # Andrés Sánchez
            "monto": Decimal("3500000"),  # 3.5 millones
            "tasa_interes": Decimal("2.3"),
            "plazo_meses": 18,
            "fecha_inicio": date.today() - timedelta(days=350),  # 11.5 meses atrás
            "origen": "socio",
            "socio_id": socios[0].id,  # María González
            "estado": "pagado",
            "observaciones": "Préstamo de socio pagado completamente"
        },
    ]

    prestamos = []
    for prestamo_data in prestamos_data:
        prestamo = Prestamo(**prestamo_data)

        # Calcular valores automáticos
        prestamo.numero_cuotas = prestamo.plazo_meses
        prestamo.valor_cuota = prestamo.calcular_cuota()
        prestamo.total_intereses = round((prestamo.valor_cuota * prestamo.numero_cuotas) - float(prestamo.monto), 2)
        prestamo.total_pagar = prestamo.valor_cuota * prestamo.numero_cuotas
        prestamo.saldo_pendiente = prestamo.total_pagar if prestamo.estado == "activo" else 0

        # Redondear valores
        prestamo.total_intereses = round(prestamo.total_intereses, 2)
        prestamo.total_pagar = round(prestamo.total_pagar, 2)
        prestamo.saldo_pendiente = round(prestamo.saldo_pendiente, 2)

        db.add(prestamo)
        prestamos.append(prestamo)

        # Si es préstamo de socio, reducir capital del socio
        if prestamo.origen == "socio" and prestamo.socio_id:
            socio = db.query(Socio).filter(Socio.id == prestamo.socio_id).first()
            if socio:
                socio.capital_actual = float(socio.capital_actual) - float(prestamo.monto)

    db.commit()
    print(f"✅ {len(prestamos)} préstamos creados correctamente")
    return prestamos

def create_pagos(db, prestamos, admin_user):
    """Crear pagos de préstamos"""
    print("💳 Creando pagos de préstamos...")

    pagos_creados = 0

    for prestamo in prestamos:
        if prestamo.estado == "pagado":
            # Para préstamos pagados, crear todos los pagos
            fecha_pago = prestamo.fecha_inicio
            cuota_numero = 1

            while cuota_numero <= prestamo.numero_cuotas:
                # Simular algunos pagos atrasados
                if cuota_numero in [3, 7]:  # Simular atrasos
                    fecha_pago = fecha_pago + timedelta(days=35)  # 5 días de atraso
                else:
                    fecha_pago = fecha_pago + timedelta(days=30)

                pago = Pago(
                    prestamo_id=prestamo.id,
                    numero_cuota=cuota_numero,
                    fecha_pago=fecha_pago,
                    monto_pagado=prestamo.valor_cuota,
                    tipo_pago="cuota",
                    metodo_pago=random.choice(["efectivo", "transferencia", "cheque"]),
                    referencia_pago=f"REC-{prestamo.id}-{cuota_numero:03d}",
                    observaciones=f"Pago cuota {cuota_numero}"
                )

                # Calcular intereses y capital
                intereses = round(float(prestamo.monto) * (float(prestamo.tasa_interes) / 100), 2)
                capital = round(float(prestamo.valor_cuota) - intereses, 2)

                pago.intereses_pagados = intereses
                pago.capital_pagado = capital

                db.add(pago)
                pagos_creados += 1

                # Actualizar saldo del préstamo
                prestamo.saldo_pendiente = max(0, prestamo.saldo_pendiente - pago.monto_pagado)
                prestamo.cuotas_pagadas += 1

                cuota_numero += 1

        else:
            # Para préstamos activos, crear algunos pagos
            num_pagos = random.randint(2, prestamo.numero_cuotas - 3)  # Dejar algunos pendientes
            fecha_pago = prestamo.fecha_inicio
            cuota_numero = 1

            while cuota_numero <= num_pagos:
                # Algunos pagos con atraso
                if random.choice([True, False]) and cuota_numero > 1:
                    fecha_pago = fecha_pago + timedelta(days=32)  # 2 días de atraso
                else:
                    fecha_pago = fecha_pago + timedelta(days=30)

                pago = Pago(
                    prestamo_id=prestamo.id,
                    numero_cuota=cuota_numero,
                    fecha_pago=fecha_pago,
                    monto_pagado=prestamo.valor_cuota,
                    tipo_pago="cuota",
                    metodo_pago=random.choice(["efectivo", "transferencia", "cheque"]),
                    referencia_pago=f"REC-{prestamo.id}-{cuota_numero:03d}",
                    observaciones=f"Pago cuota {cuota_numero}"
                )

                # Calcular intereses y capital
                intereses = round(float(prestamo.monto) * (float(prestamo.tasa_interes) / 100), 2)
                capital = round(float(prestamo.valor_cuota) - intereses, 2)

                pago.intereses_pagados = intereses
                pago.capital_pagado = capital

                db.add(pago)
                pagos_creados += 1

                # Actualizar saldo del préstamo
                prestamo.saldo_pendiente = max(0, prestamo.saldo_pendiente - pago.monto_pagado)
                prestamo.cuotas_pagadas += 1

                cuota_numero += 1

    db.commit()
    print(f"✅ {pagos_creados} pagos de préstamos creados correctamente")

def create_pagos_socios(db, socios, admin_user):
    """Crear pagos/movimientos de socios"""
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

        # Crear algunos retiros de ganancias (simulando)
        num_ganancias = random.randint(1, 3)
        fecha_base = socio.creado_en.date() if socio.creado_en else date.today() - timedelta(days=300)

        for i in range(num_ganancias):
            fecha_ganancia = fecha_base + timedelta(days=random.randint(60, 300))
            monto_ganancia = Decimal(str(random.randint(500000, 2000000)))  # 0.5 a 2 millones

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

def main():
    """Función principal para resetear y llenar la base de datos"""
    print("🚀 INICIANDO RESET COMPLETO DE BASE DE DATOS")
    print("=" * 50)

    # Crear sesión de base de datos
    db = SessionLocal()

    try:
        # Resetear base de datos
        reset_database()

        # Crear datos en orden de dependencias
        create_roles(db)
        create_users(db)
        create_configurations(db)
        clientes = create_clientes(db)
        socios = create_socios(db)

        # Obtener usuario admin para los pagos
        admin_user = db.query(Usuario).filter(Usuario.username == "admin").first()

        prestamos = create_prestamos(db, clientes, socios)
        create_pagos(db, prestamos, admin_user)
        create_pagos_socios(db, socios, admin_user)

        print()
        print("🎉 ¡BASE DE DATOS RESETADA Y LLENADA EXITOSAMENTE!")
        print("=" * 50)
        print("📊 RESUMEN DE DATOS CREADOS:")
        print(f"   👥 Usuarios: 2 (admin, digitador)")
        print(f"   👨‍👩‍👧‍👦 Clientes: {len(clientes)}")
        print(f"   🤝 Socios: {len(socios)}")
        print(f"   💰 Préstamos: {len(prestamos)}")
        print()
        print("🔐 USUARIOS DE ACCESO:")
        print("   👑 Admin: admin / admin123")
        print("   👤 Digitador: digitador / digitador123")
        print()
        print("✨ El sistema está listo para pruebas completas!")

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()

if __name__ == "__main__":
    main()
