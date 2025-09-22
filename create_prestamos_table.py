"""
Script para crear las tablas de préstamos y pagos en la base de datos existente
"""

from app.core.database import SessionLocal, engine, Base
from app.models.prestamo import Prestamo
from app.models.pago import Pago
from app.models.cliente import Cliente
from datetime import datetime, timedelta
import random

def create_prestamos_table():
    """Crear tablas de préstamos y pagos y agregar datos de ejemplo"""

    # Crear tablas
    Prestamo.__table__.create(bind=engine, checkfirst=True)
    Pago.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()

    try:
        # Verificar si ya existen préstamos
        existing_prestamos = db.query(Prestamo).count()
        if existing_prestamos > 0:
            print("Los préstamos ya están creados en la base de datos.")
            return

        print("Creando tablas de préstamos y pagos y datos de ejemplo...")

        # Obtener clientes existentes
        clientes = db.query(Cliente).filter(Cliente.activo == 1).all()
        if not clientes:
            print("No hay clientes activos. Primero debe crear clientes.")
            return

        # Crear préstamos de ejemplo
        prestamos_data = [
            {
                "cliente_id": clientes[0].id if len(clientes) > 0 else 1,
                "monto": 2000000.00,  # 2 millones de pesos
                "tasa_interes": 2.5,  # 2.5% mensual
                "plazo_meses": 12,    # 12 meses
                "fecha_inicio": datetime.now() - timedelta(days=60),
                "observaciones": "Préstamo para capital de trabajo"
            },
            {
                "cliente_id": clientes[1].id if len(clientes) > 1 else 1,
                "monto": 1500000.00,  # 1.5 millones de pesos
                "tasa_interes": 2.0,  # 2.0% mensual
                "plazo_meses": 8,     # 8 meses
                "fecha_inicio": datetime.now() - timedelta(days=30),
                "observaciones": "Préstamo personal"
            },
            {
                "cliente_id": clientes[2].id if len(clientes) > 2 else 1,
                "monto": 3000000.00,  # 3 millones de pesos
                "tasa_interes": 3.0,  # 3.0% mensual
                "plazo_meses": 18,    # 18 meses
                "fecha_inicio": datetime.now() - timedelta(days=90),
                "observaciones": "Préstamo para inversión en negocio"
            }
        ]

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

        # Crear algunos pagos de ejemplo para los préstamos
        for i, prestamo in enumerate(prestamos_creados):
            # Determinar cuántas cuotas han sido pagadas (simular progreso)
            cuotas_pagadas = min(prestamo.numero_cuotas, random.randint(1, prestamo.numero_cuotas // 2 + 1))

            for cuota_num in range(1, cuotas_pagadas + 1):
                # Crear pago con fecha correspondiente
                fecha_pago = prestamo.fecha_inicio + timedelta(days=30 * cuota_num)

                pago = Pago(
                    prestamo_id=prestamo.id,
                    fecha_pago=fecha_pago,
                    monto_pagado=prestamo.valor_cuota,
                    tipo_pago="cuota",
                    numero_cuota=cuota_num,
                    metodo_pago=random.choice(["efectivo", "transferencia", "cheque"]),
                    referencia_pago=f"REC-{prestamo.id:03d}-{cuota_num:02d}",
                    capital_pagado=round(prestamo.monto / prestamo.numero_cuotas, 2),
                    intereses_pagados=round(prestamo.total_intereses / prestamo.numero_cuotas, 2),
                    observaciones=f"Pago cuota {cuota_num} del préstamo #{prestamo.id}"
                )

                db.add(pago)

                # Actualizar el préstamo
                prestamo.cuotas_pagadas += 1
                prestamo.saldo_pendiente -= prestamo.valor_cuota

                # Si ya no queda saldo, marcar como pagado
                if prestamo.saldo_pendiente <= 0:
                    prestamo.estado = "pagado"
                    prestamo.saldo_pendiente = 0

        db.commit()

        print("Créditos creados:")
        for prestamo in prestamos_creados:
            print(f"  - Crédito #{prestamo.id}: ${prestamo.monto:,.0f} a {prestamo.tasa_interes}% por {prestamo.plazo_meses} meses")
            print(f"    Cuota: ${prestamo.valor_cuota:,.0f}, Estado: {prestamo.estado}")

        print("\nPagos registrados para simular progreso de los créditos.")
        print("\nTablas de créditos y pagos creadas exitosamente!")

    except Exception as e:
        print(f"Error creando tablas de créditos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_prestamos_table()
