"""
Script para crear datos de prueba realistas en Credexa
Elimina datos existentes y crea nuevos datos que cubren todos los escenarios posibles
"""

from app.core.database import SessionLocal, engine, Base
from app.models.prestamo import Prestamo
from app.models.pago import Pago
from app.models.cliente import Cliente
from datetime import datetime, timedelta
from decimal import Decimal
import random

def clean_and_create_realistic_test_data():
    """Limpiar completamente la base de datos y crear datos de prueba realistas"""

    db = SessionLocal()

    try:
        print("🧹 Eliminando datos existentes...")

        # Eliminar todos los pagos, préstamos y clientes existentes
        db.query(Pago).delete()
        db.query(Prestamo).delete()
        db.query(Cliente).delete()
        db.commit()

        print("✅ Datos anteriores eliminados.")
        print("🏗️ Creando nuevos datos de prueba realistas...")

        # Crear clientes realistas
        clientes_data = [
            {
                "nombre_completo": "María González Pérez",
                "cedula": "12345678",
                "telefono": "3001234567",
                "email": "maria.gonzalez@email.com",
                "direccion": "Calle 123 #45-67, Bogotá",
                "fecha_nacimiento": datetime(1985, 3, 15),
                "ocupacion": "Comerciante",
                "ingresos_mensuales": 2500000,
                "referencias_personales": "Juan Pérez (hermano) - Tel: 3012345678",
                "notas": "Cliente fiel, buen historial de pagos"
            },
            {
                "nombre_completo": "Carlos Rodríguez López",
                "cedula": "87654321",
                "telefono": "3019876543",
                "email": "carlos.rodriguez@email.com",
                "direccion": "Carrera 89 #12-34, Medellín",
                "fecha_nacimiento": datetime(1990, 7, 22),
                "ocupacion": "Empleado privado",
                "ingresos_mensuales": 1800000,
                "referencias_personales": "Ana López (madre) - Tel: 3023456789",
                "notas": "Primer préstamo, buen potencial"
            },
            {
                "nombre_completo": "Ana Martínez Silva",
                "cedula": "11223344",
                "telefono": "3024567890",
                "email": "ana.martinez@email.com",
                "direccion": "Avenida 68 #45-12, Cali",
                "fecha_nacimiento": datetime(1978, 11, 8),
                "ocupacion": "Profesional independiente",
                "ingresos_mensuales": 3200000,
                "referencias_personales": "Pedro Silva (amigo) - Tel: 3034567890",
                "notas": "Cliente premium, alta capacidad de pago"
            },
            {
                "nombre_completo": "Luis Hernández García",
                "cedula": "55667788",
                "telefono": "3035678901",
                "email": "luis.hernandez@email.com",
                "direccion": "Transversal 45 #67-89, Barranquilla",
                "fecha_nacimiento": datetime(1982, 5, 30),
                "ocupacion": "Empresario",
                "ingresos_mensuales": 4500000,
                "referencias_personales": "María García (esposa) - Tel: 3045678901",
                "notas": "Cliente corporativo, requiere montos altos"
            },
            {
                "nombre_completo": "Patricia Ramírez Torres",
                "cedula": "99001122",
                "telefono": "3046789012",
                "email": "patricia.ramirez@email.com",
                "direccion": "Diagonal 23 #34-56, Cartagena",
                "fecha_nacimiento": datetime(1988, 9, 14),
                "ocupacion": "Docente",
                "ingresos_mensuales": 1600000,
                "referencias_personales": "Roberto Torres (padre) - Tel: 3056789012",
                "notas": "Cliente con buen historial académico"
            },
            {
                "nombre_completo": "Miguel Ángel Castro",
                "cedula": "33445566",
                "telefono": "3057890123",
                "email": "miguel.castro@email.com",
                "direccion": "Calle 45 #23-12, Bucaramanga",
                "fecha_nacimiento": datetime(1975, 12, 3),
                "ocupacion": "Médico",
                "ingresos_mensuales": 5500000,
                "referencias_personales": "Carmen Castro (esposa) - Tel: 3067890123",
                "notas": "Profesional de altos ingresos, bajo riesgo"
            },
            {
                "nombre_completo": "Sandra Valencia Muñoz",
                "cedula": "77889900",
                "telefono": "3068901234",
                "email": "sandra.valencia@email.com",
                "direccion": "Carrera 15 #89-01, Pereira",
                "fecha_nacimiento": datetime(1983, 1, 25),
                "ocupacion": "Abogada",
                "ingresos_mensuales": 2800000,
                "referencias_personales": "Diego Muñoz (hermano) - Tel: 3078901234",
                "notas": "Profesional del derecho, buen historial"
            },
            {
                "nombre_completo": "Jorge Luis Morales",
                "cedula": "22334455",
                "telefono": "3079012345",
                "email": "jorge.morales@email.com",
                "direccion": "Avenida 9 #67-45, Manizales",
                "fecha_nacimiento": datetime(1970, 6, 18),
                "ocupacion": "Ingeniero",
                "ingresos_mensuales": 3500000,
                "referencias_personales": "Lucía Morales (esposa) - Tel: 3089012345",
                "notas": "Cliente antiguo, muy confiable"
            }
        ]

        # Crear clientes
        clientes_creados = []
        for cliente_data in clientes_data:
            cliente = Cliente(**cliente_data, activo=True)
            db.add(cliente)
            clientes_creados.append(cliente)

        db.commit()
        print(f"✅ {len(clientes_creados)} clientes creados.")

        # Crear préstamos realistas con diferentes escenarios
        prestamos_data = [
            # Crédito PAGADO COMPLETAMENTE (María González)
            {
                "cliente_id": clientes_creados[0].id,
                "monto": 2500000.00,
                "tasa_interes": 2.5,
                "plazo_meses": 12,
                "fecha_inicio": datetime.now() - timedelta(days=400),  # Hace 13 meses
                "observaciones": "Crédito para ampliación de tienda - PAGADO COMPLETAMENTE"
            },
            # Crédito ACTIVO al día (Carlos Rodríguez)
            {
                "cliente_id": clientes_creados[1].id,
                "monto": 1800000.00,
                "tasa_interes": 2.2,
                "plazo_meses": 10,
                "fecha_inicio": datetime.now() - timedelta(days=120),  # Hace 4 meses
                "observaciones": "Crédito personal para educación - PAGOS AL DÍA"
            },
            # Crédito EN MORA (Ana Martínez)
            {
                "cliente_id": clientes_creados[2].id,
                "monto": 3000000.00,
                "tasa_interes": 2.8,
                "plazo_meses": 15,
                "fecha_inicio": datetime.now() - timedelta(days=200),  # Hace 6.5 meses
                "observaciones": "Crédito para consultoría - EN MORA (3 cuotas pendientes)"
            },
            # Crédito PAGADO COMPLETAMENTE (Luis Hernández)
            {
                "cliente_id": clientes_creados[3].id,
                "monto": 5000000.00,
                "tasa_interes": 2.0,
                "plazo_meses": 20,
                "fecha_inicio": datetime.now() - timedelta(days=650),  # Hace 21.5 meses
                "observaciones": "Crédito corporativo para expansión - PAGADO COMPLETAMENTE"
            },
            # Crédito ACTIVO con algunos pagos (Patricia Ramírez)
            {
                "cliente_id": clientes_creados[4].id,
                "monto": 1200000.00,
                "tasa_interes": 2.3,
                "plazo_meses": 8,
                "fecha_inicio": datetime.now() - timedelta(days=90),  # Hace 3 meses
                "observaciones": "Crédito educativo - 2 cuotas pagadas"
            },
            # Crédito EN MORA GRAVE (Miguel Ángel Castro)
            {
                "cliente_id": clientes_creados[5].id,
                "monto": 4000000.00,
                "tasa_interes": 2.1,
                "plazo_meses": 24,
                "fecha_inicio": datetime.now() - timedelta(days=300),  # Hace 10 meses
                "observaciones": "Crédito para equipo médico - EN MORA GRAVE (6 cuotas pendientes)"
            },
            # Crédito RECIÉN APROBADO (Sandra Valencia)
            {
                "cliente_id": clientes_creados[6].id,
                "monto": 2200000.00,
                "tasa_interes": 2.4,
                "plazo_meses": 12,
                "fecha_inicio": datetime.now() - timedelta(days=15),  # Hace 15 días
                "observaciones": "Crédito para bufete jurídico - PRIMER PAGO PENDIENTE"
            },
            # Crédito PAGADO COMPLETAMENTE (Jorge Luis Morales)
            {
                "cliente_id": clientes_creados[7].id,
                "monto": 3500000.00,
                "tasa_interes": 2.6,
                "plazo_meses": 18,
                "fecha_inicio": datetime.now() - timedelta(days=580),  # Hace 19 meses
                "observaciones": "Crédito para proyecto de ingeniería - PAGADO COMPLETAMENTE"
            }
        ]

        # Crear préstamos
        prestamos_creados = []
        for prestamo_data in prestamos_data:
            prestamo = Prestamo(**prestamo_data)

            # Calcular valores automáticos
            prestamo.numero_cuotas = prestamo.plazo_meses
            prestamo.valor_cuota = prestamo.calcular_cuota()
            prestamo.total_intereses = (prestamo.valor_cuota * prestamo.numero_cuotas) - float(prestamo.monto)
            prestamo.total_pagar = prestamo.valor_cuota * prestamo.numero_cuotas
            prestamo.saldo_pendiente = prestamo.total_pagar

            # Redondear valores
            prestamo.total_intereses = round(prestamo.total_intereses, 2)
            prestamo.total_pagar = round(prestamo.total_pagar, 2)

            db.add(prestamo)
            prestamos_creados.append(prestamo)

        db.commit()
        print(f"✅ {len(prestamos_creados)} créditos creados.")

        # Crear pagos realistas para cada escenario
        metodos_pago = ["efectivo", "transferencia", "cheque", "tarjeta_debito"]
        tipos_pago = ["cuota", "abono", "extra"]

        # 1. Crédito PAGADO COMPLETAMENTE #1 (María González - 12 cuotas)
        prestamo = prestamos_creados[0]
        for cuota_num in range(1, 13):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago cuota {cuota_num} - Crédito pagado completamente"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        prestamo.estado = "pagado"
        prestamo.saldo_pendiente = 0

        # 2. Crédito ACTIVO al día #2 (Carlos Rodríguez - 4 cuotas pagadas de 10)
        prestamo = prestamos_creados[1]
        for cuota_num in range(1, 5):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago puntual cuota {cuota_num}"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        # 3. Crédito EN MORA #3 (Ana Martínez - 3 cuotas pagadas, 3 en mora)
        prestamo = prestamos_creados[2]
        for cuota_num in range(1, 4):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago cuota {cuota_num} - Último pago hace 3 meses"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        prestamo.estado = "mora"  # 3 cuotas pendientes

        # 4. Crédito PAGADO COMPLETAMENTE #4 (Luis Hernández - 20 cuotas)
        prestamo = prestamos_creados[3]
        for cuota_num in range(1, 21):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago corporativo cuota {cuota_num}"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        prestamo.estado = "pagado"
        prestamo.saldo_pendiente = 0

        # 5. Crédito ACTIVO #5 (Patricia Ramírez - 2 cuotas pagadas de 8)
        prestamo = prestamos_creados[4]
        for cuota_num in range(1, 3):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago educativo cuota {cuota_num}"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        # 6. Crédito EN MORA GRAVE #6 (Miguel Ángel Castro - 4 cuotas pagadas, 6 en mora)
        prestamo = prestamos_creados[5]
        for cuota_num in range(1, 5):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago médico cuota {cuota_num} - Crédito en mora grave"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        prestamo.estado = "mora"  # 6 cuotas pendientes

        # 7. Crédito RECIÉN APROBADO #7 (Sandra Valencia - sin pagos aún)
        prestamo = prestamos_creados[6]
        # No se crean pagos, está recién aprobado

        # 8. Crédito PAGADO COMPLETAMENTE #8 (Jorge Luis Morales - 18 cuotas)
        prestamo = prestamos_creados[7]
        for cuota_num in range(1, 19):
            fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

            pago = Pago(
                prestamo_id=prestamo.id,
                fecha_pago=fecha_pago,
                monto_pagado=Decimal(str(prestamo.valor_cuota)),
                tipo_pago="cuota",
                numero_cuota=cuota_num,
                metodo_pago=random.choice(metodos_pago),
                referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                capital_pagado=Decimal(str(round(float(prestamo.monto) / prestamo.numero_cuotas, 2))),
                intereses_pagados=Decimal(str(round(float(prestamo.total_intereses) / prestamo.numero_cuotas, 2))),
                observaciones=f"Pago ingeniería cuota {cuota_num}"
            )
            db.add(pago)
            prestamo.cuotas_pagadas += 1
            prestamo.saldo_pendiente -= prestamo.valor_cuota

        prestamo.estado = "pagado"
        prestamo.saldo_pendiente = 0

        # Agregar algunos pagos extras y abonos para mayor realismo
        # Abono extra al crédito #2 (Carlos Rodríguez)
        prestamo = prestamos_creados[1]
        abono_extra = Pago(
            prestamo_id=prestamo.id,
            fecha_pago=datetime.now() - timedelta(days=10),
            monto_pagado=Decimal('50000.00'),
            tipo_pago="abono",
            numero_cuota=5,
            metodo_pago="transferencia",
            referencia_pago=f"ABONO-{prestamo.id:03d}-EXTRA",
            capital_pagado=Decimal('50000.00'),
            intereses_pagados=Decimal('0'),
            observaciones="Abono extraordinario por prima"
        )
        db.add(abono_extra)
        prestamo.saldo_pendiente -= Decimal('50000.00')

        # Pago parcial de mora del crédito #3 (Ana Martínez)
        prestamo = prestamos_creados[2]
        monto_parcial = float(prestamo.valor_cuota) * 0.5
        pago_parcial = Pago(
            prestamo_id=prestamo.id,
            fecha_pago=datetime.now() - timedelta(days=5),
            monto_pagado=Decimal(str(monto_parcial)),  # Pago parcial
            tipo_pago="abono",
            numero_cuota=4,
            metodo_pago="efectivo",
            referencia_pago=f"PARCIAL-{prestamo.id:03d}-MORA",
            capital_pagado=Decimal(str(round(monto_parcial, 2))),
            intereses_pagados=Decimal('0'),
            observaciones="Pago parcial de cuota en mora"
        )
        db.add(pago_parcial)
        prestamo.saldo_pendiente -= pago_parcial.monto_pagado

        db.commit()

        # Contar pagos creados
        total_pagos = db.query(Pago).count()

        print(f"✅ {total_pagos} pagos registrados.")

        # Resumen final
        print("\n📊 RESUMEN DE DATOS CREADOS:")
        print(f"👥 Clientes: {len(clientes_creados)}")
        print(f"💰 Créditos: {len(prestamos_creados)}")
        print(f"💳 Pagos: {total_pagos}")

        print("\n🏦 ESTADO DE CRÉDITOS:")
        estados = {}
        for prestamo in prestamos_creados:
            estado = prestamo.estado
            if estado not in estados:
                estados[estado] = 0
            estados[estado] += 1

        for estado, cantidad in estados.items():
            emoji = {"activo": "🟢", "pagado": "✅", "mora": "🔴"}.get(estado, "⚪")
            print(f"  {emoji} {estado.upper()}: {cantidad} créditos")

        print("\n🎯 ESCENARIOS CUBIERTOS:")
        print("  ✅ Créditos completamente pagados")
        print("  ✅ Créditos activos al día")
        print("  ✅ Créditos en mora leve")
        print("  ✅ Créditos en mora grave")
        print("  ✅ Créditos recién aprobados")
        print("  ✅ Pagos puntuales y atrasados")
        print("  ✅ Abonos extraordinarios")
        print("  ✅ Pagos parciales")

        print("\n🎉 ¡Datos de prueba realistas creados exitosamente!")
        print("💡 Ahora puedes explorar todas las funcionalidades de Credexa con datos representativos.")

    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_and_create_realistic_test_data()
