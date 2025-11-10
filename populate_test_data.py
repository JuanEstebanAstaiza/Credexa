#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de prueba
"""

import sys
import os
sys.path.append('.')

from app.core.database import get_db
from app.models import Empresa, Usuario, Cliente, Socio, Prestamo, Pago, Rol
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import random

def create_test_data():
    """Crear datos de prueba para todas las empresas"""

    db = next(get_db())

    try:
        # Obtener todas las empresas
        empresas = db.query(Empresa).all()
        print(f"Encontradas {len(empresas)} empresas")

        for empresa in empresas:
            print(f"\nPoblando datos para empresa: {empresa.nombre} (ID: {empresa.id})")

            # Crear usuarios de prueba para cada empresa
            create_test_users(db, empresa)

            # Crear clientes de prueba
            create_test_clients(db, empresa)

            # Crear socios de prueba
            create_test_socios(db, empresa)

            # Crear préstamos de prueba
            create_test_prestamos(db, empresa)

        print("\nTodos los datos de prueba han sido creados exitosamente!")
        print("\nResumen de datos creados:")
        for empresa in empresas:
            clientes_count = db.query(Cliente).filter(Cliente.empresa_id == empresa.id).count()
            socios_count = db.query(Socio).filter(Socio.empresa_id == empresa.id).count()
            prestamos_count = db.query(Prestamo).filter(Prestamo.empresa_id == empresa.id).count()
            usuarios_count = db.query(Usuario).filter(Usuario.empresa_id == empresa.id).count()

            print(f"  {empresa.nombre}:")
            print(f"    - {usuarios_count} usuarios")
            print(f"    - {clientes_count} clientes")
            print(f"    - {socios_count} socios")
            print(f"    - {prestamos_count} prestamos")

    except Exception as e:
        print(f"Error creando datos de prueba: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def create_test_users(db, empresa):
    """Crear usuarios de prueba para una empresa"""
    test_users = [
        {
            'nombre_completo': f'Digitador {empresa.slug}',
            'username': f'digitador_{empresa.slug}',
            'email': f'digitador@{empresa.slug}.com',
            'password': 'digitador123',
            'rol': 'digitador'
        },
        {
            'nombre_completo': f'Analista {empresa.slug}',
            'username': f'analista_{empresa.slug}',
            'email': f'analista@{empresa.slug}.com',
            'password': 'analista123',
            'rol': 'analista'
        }
    ]

    for user_data in test_users:
        # Verificar si ya existe
        existing_user = db.query(Usuario).filter(
            Usuario.email == user_data['email']
        ).first()

        if not existing_user:
            # Obtener rol
            rol = db.query(Rol).filter(Rol.nombre == user_data['rol']).first()

            if rol:
                new_user = Usuario(
                    nombre_completo=user_data['nombre_completo'],
                    username=user_data['username'],
                    email=user_data['email'],
                    hashed_password=get_password_hash(user_data['password']),
                    empresa_id=empresa.id,
                    rol_id=rol.id,
                    activo=True
                )
                db.add(new_user)
                print(f"    Usuario creado: {user_data['email']}")

def create_test_clients(db, empresa):
    """Crear clientes de prueba con diferentes ingresos mensuales"""
    test_clients = [
        {
            'nombre_completo': 'María González Pérez',
            'cedula': '12345678',
            'telefono': '3101234567',
            'email': 'maria.gonzalez@email.com',
            'direccion': 'Calle 10 # 15-20, Bogotá',
            'ocupacion': 'Profesora',
            'ingresos_mensuales': 2500000,
            'referencias_personales': 'Juan Pérez (hermano) - Tel: 3119876543'
        },
        {
            'nombre_completo': 'Carlos Rodríguez López',
            'cedula': '87654321',
            'telefono': '3207654321',
            'email': 'carlos.rodriguez@email.com',
            'direccion': 'Carrera 7 # 25-15, Medellín',
            'ocupacion': 'Ingeniero Civil',
            'ingresos_mensuales': 4500000,
            'referencias_personales': 'Ana López (esposa) - Tel: 3224567890'
        },
        {
            'nombre_completo': 'Ana Martínez Silva',
            'cedula': '11223344',
            'telefono': '3012345678',
            'email': 'ana.martinez@email.com',
            'direccion': 'Avenida 68 # 45-30, Bogotá',
            'ocupacion': 'Médica',
            'ingresos_mensuales': 6500000,
            'referencias_personales': 'Pedro Silva (padre) - Tel: 3156789012'
        },
        {
            'nombre_completo': 'Luis Hernández Torres',
            'cedula': '44332211',
            'telefono': '3159876543',
            'email': 'luis.hernandez@email.com',
            'direccion': 'Calle 50 # 10-25, Cali',
            'ocupacion': 'Contador',
            'ingresos_mensuales': 3200000,
            'referencias_personales': 'María Torres (madre) - Tel: 3187654321'
        },
        {
            'nombre_completo': 'Sofia Castro Morales',
            'cedula': '99887766',
            'telefono': '3223456789',
            'email': 'sofia.castro@email.com',
            'direccion': 'Carrera 15 # 85-40, Barranquilla',
            'ocupacion': 'Abogada',
            'ingresos_mensuales': 5500000,
            'referencias_personales': 'Roberto Morales (esposo) - Tel: 3198765432'
        },
        {
            'nombre_completo': 'Diego Ramírez Ortega',
            'cedula': '55667788',
            'telefono': '3045678901',
            'email': 'diego.ramirez@email.com',
            'direccion': 'Transversal 9 # 32-15, Cartagena',
            'ocupacion': 'Arquitecto',
            'ingresos_mensuales': 3800000,
            'referencias_personales': 'Carmen Ortega (hermana) - Tel: 3165432198'
        },
        {
            'nombre_completo': 'Valentina López Mendoza',
            'cedula': '33445566',
            'telefono': '3178901234',
            'email': 'valentina.lopez@email.com',
            'direccion': 'Diagonal 5 # 18-35, Bucaramanga',
            'ocupacion': 'Psicóloga',
            'ingresos_mensuales': 2800000,
            'referencias_personales': 'Fernando Mendoza (padre) - Tel: 3123456789'
        },
        {
            'nombre_completo': 'Mateo Vargas Ruiz',
            'cedula': '77889900',
            'telefono': '3189012345',
            'email': 'mateo.vargas@email.com',
            'direccion': 'Calle 12 # 5-40, Pereira',
            'ocupacion': 'Desarrollador de Software',
            'ingresos_mensuales': 4200000,
            'referencias_personales': 'Isabella Ruiz (madre) - Tel: 3190123456'
        },
        {
            'nombre_completo': 'Camila Fernández Castro',
            'cedula': '00112233',
            'telefono': '3190123456',
            'email': 'camila.fernandez@email.com',
            'direccion': 'Avenida 2N # 7-45, Manizales',
            'ocupacion': 'Farmacéutica',
            'ingresos_mensuales': 3600000,
            'referencias_personales': 'Diego Castro (hermano) - Tel: 3201234567'
        },
        {
            'nombre_completo': 'Santiago Morales Peña',
            'cedula': '44556677',
            'telefono': '3201234567',
            'email': 'santiago.morales@email.com',
            'direccion': 'Carrera 8 # 12-20, Ibagué',
            'ocupacion': 'Dentista',
            'ingresos_mensuales': 4800000,
            'referencias_personales': 'Lucía Peña (esposa) - Tel: 3212345678'
        }
    ]

    for client_data in test_clients:
        # Verificar si ya existe
        existing_client = db.query(Cliente).filter(
            Cliente.cedula == client_data['cedula'],
            Cliente.empresa_id == empresa.id
        ).first()

        if not existing_client:
            new_client = Cliente(
                **client_data,
                empresa_id=empresa.id,
                activo=1
            )
            db.add(new_client)

    db.commit()
    print(f"    {len(test_clients)} clientes creados para {empresa.nombre}")

def create_test_socios(db, empresa):
    """Crear socios de prueba"""
    test_socios = [
        {
            'nombre_completo': f'Juan Pérez {empresa.slug.title()}',
            'cedula': f'1000000{empresa.id}1',
            'telefono': f'31010000{empresa.id}1',
            'email': f'juan.perez@{empresa.slug}.com',
            'direccion': f'Calle Principal #{empresa.id}0-10, Ciudad',
            'ocupacion': 'Empresario',
            'ingresos_mensuales': 8000000,
            'capital_inicial': 50000000,
            'porcentaje_participacion': 40.0
        },
        {
            'nombre_completo': f'María García {empresa.slug.title()}',
            'cedula': f'1000000{empresa.id}2',
            'telefono': f'31010000{empresa.id}2',
            'email': f'maria.garcia@{empresa.slug}.com',
            'direccion': f'Avenida Central #{empresa.id}5-25, Ciudad',
            'ocupacion': 'Inversionista',
            'ingresos_mensuales': 6500000,
            'capital_inicial': 30000000,
            'porcentaje_participacion': 30.0
        },
        {
            'nombre_completo': f'Pedro Rodríguez {empresa.slug.title()}',
            'cedula': f'1000000{empresa.id}3',
            'telefono': f'31010000{empresa.id}3',
            'email': f'pedro.rodriguez@{empresa.slug}.com',
            'direccion': f'Carrera 7 #{empresa.id}8-15, Ciudad',
            'ocupacion': 'Comerciante',
            'ingresos_mensuales': 4500000,
            'capital_inicial': 20000000,
            'porcentaje_participacion': 30.0
        }
    ]

    for socio_data in test_socios:
        # Verificar si ya existe
        existing_socio = db.query(Socio).filter(
            Socio.cedula == socio_data['cedula'],
            Socio.empresa_id == empresa.id
        ).first()

        if not existing_socio:
            new_socio = Socio(
                **socio_data,
                empresa_id=empresa.id,
                activo=1
            )
            db.add(new_socio)

    db.commit()
    print(f"    {len(test_socios)} socios creados para {empresa.nombre}")

def create_test_prestamos(db, empresa):
    """Crear préstamos de prueba"""
    # Obtener clientes de esta empresa
    clientes = db.query(Cliente).filter(Cliente.empresa_id == empresa.id).limit(5).all()

    if not clientes:
        return

    prestamos_creados = 0
    for cliente in clientes:
        # Crear 1-2 préstamos por cliente
        num_prestamos = random.randint(1, 2)

        for i in range(num_prestamos):
            monto = random.choice([1000000, 2000000, 3000000, 5000000])
            plazo_meses = random.choice([6, 12, 18, 24])
            tasa_interes = random.choice([1.5, 2.0, 2.5, 3.0])

            # Calcular fecha de creación (últimos 6 meses)
            dias_atras = random.randint(0, 180)
            fecha_creacion = datetime.now() - timedelta(days=dias_atras)

            # Calcular valores básicos del préstamo
            valor_cuota = (monto * (1 + tasa_interes/100 * plazo_meses)) / plazo_meses
            total_intereses = monto * (tasa_interes/100) * (plazo_meses/12)  # Interés simple mensual
            total_pagar = monto + total_intereses

            new_prestamo = Prestamo(
                cliente_id=cliente.id,
                empresa_id=empresa.id,
                monto=monto,
                plazo_meses=plazo_meses,
                tasa_interes=tasa_interes,
                fecha_inicio=fecha_creacion.date(),
                valor_cuota=valor_cuota,
                numero_cuotas=plazo_meses,
                total_intereses=total_intereses,
                total_pagar=total_pagar,
                saldo_pendiente=total_pagar,
                cuotas_pagadas=0,
                estado='activo',
                es_refinanciacion=0
            )
            db.add(new_prestamo)
            prestamos_creados += 1

            # Crear algunos pagos para este préstamo
            create_test_pagos(db, new_prestamo, fecha_creacion)

    db.commit()
    print(f"    {prestamos_creados} prestamos creados para {empresa.nombre}")

def create_test_pagos(db, prestamo, fecha_inicio):
    """Crear pagos de prueba para un préstamo"""
    pagos_creados = 0

    # Crear entre 1-3 pagos por préstamo
    num_pagos = random.randint(1, 3)

    for i in range(num_pagos):
        # Monto del pago (cuota mensual aproximada)
        cuota_mensual = prestamo.monto / prestamo.plazo_meses
        monto_pago = cuota_mensual * (0.8 + random.random() * 0.4)  # ±20% variación

        # Fecha del pago
        dias_despues = (i + 1) * 30 + random.randint(-5, 5)  # Aproximadamente mensual
        fecha_pago = fecha_inicio + timedelta(days=dias_despues)

        new_pago = Pago(
            prestamo_id=prestamo.id,
            empresa_id=prestamo.empresa_id,
            fecha_pago=fecha_pago.date(),
            monto_pagado=int(monto_pago),
            tipo_pago='cuota',
            capital_pagado=int(monto_pago * 0.8),  # 80% al capital
            intereses_pagados=int(monto_pago * 0.2),  # 20% a intereses
            numero_cuota=i+1,
            metodo_pago=random.choice(['efectivo', 'transferencia', 'cheque']),
            referencia_pago=f'Pago-{prestamo.id}-{i+1}',
            observaciones=f'Pago #{i+1} del prestamo {prestamo.id}'
        )
        db.add(new_pago)
        pagos_creados += 1

    db.commit()
    print(f"      {pagos_creados} pagos creados para prestamo #{prestamo.id}")

if __name__ == "__main__":
    print("Iniciando poblacion de datos de prueba...")
    create_test_data()
    print("\nProceso completado exitosamente!")
