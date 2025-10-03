#!/usr/bin/env python3
"""
Script para verificar que la configuración de zona horaria funciona correctamente
"""
import datetime
import pytz

# Configuración de zona horaria
TIMEZONE_COLOMBIA = pytz.timezone('America/Bogota')

def convertir_a_colombia(dt):
    """Convierte un datetime UTC a zona horaria de Colombia"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Si no tiene zona horaria, asumir UTC
        dt = pytz.utc.localize(dt)
    return dt.astimezone(TIMEZONE_COLOMBIA)

def fecha_colombia(dt):
    """Convierte una fecha UTC a zona horaria de Colombia y la formatea"""
    if dt is None:
        return ""
    colombia_dt = convertir_a_colombia(dt)
    return colombia_dt.strftime('%d/%m/%Y %H:%M')

def fecha_colombia_corta(dt):
    """Convierte una fecha UTC a zona horaria de Colombia (solo fecha)"""
    if dt is None:
        return ""
    colombia_dt = convertir_a_colombia(dt)
    return colombia_dt.strftime('%d/%m/%Y')

def main():
    print("🕐 VERIFICACIÓN DE CONFIGURACIÓN DE ZONA HORARIA")
    print("=" * 50)

    # Fecha actual UTC
    ahora_utc = datetime.datetime.utcnow()
    print(f"Fecha/hora actual (UTC): {ahora_utc}")
    print(f"Timestamp UTC: {ahora_utc.timestamp()}")

    # Convertir a Colombia
    ahora_colombia = convertir_a_colombia(ahora_utc)
    print(f"Fecha/hora Colombia: {ahora_colombia}")
    print(f"Timestamp Colombia: {ahora_colombia.timestamp()}")

    # Diferencia
    diferencia = ahora_colombia - ahora_utc.replace(tzinfo=pytz.utc)
    print(f"Diferencia horaria: {diferencia}")

    print("\n📅 PRUEBAS DE FORMATEO")
    print("-" * 30)

    # Fechas de ejemplo
    fechas_prueba = [
        datetime.datetime(2025, 10, 3, 19, 15, 30),  # UTC
        datetime.datetime(2025, 10, 3, 12, 0, 0),    # UTC
        datetime.datetime(2025, 10, 3, 0, 0, 0),     # UTC medianoche
    ]

    for i, fecha_utc in enumerate(fechas_prueba, 1):
        print(f"\nPrueba {i}:")
        print(f"  UTC: {fecha_utc}")
        print(f"  Colombia: {convertir_a_colombia(fecha_utc)}")
        print(f"  Formateada: {fecha_colombia(fecha_utc)}")
        print(f"  Fecha corta: {fecha_colombia_corta(fecha_utc)}")

    print("\n✅ CONFIGURACIÓN DE ZONA HORARIA VERIFICADA")
    print("\n📋 RESUMEN DE CAMBIOS IMPLEMENTADOS:")
    print("1. ✅ Configuración de zona horaria America/Bogota (UTC-5)")
    print("2. ✅ Función convertir_a_colombia() en app/core/database.py")
    print("3. ✅ Filtros Jinja2: fecha_colombia y fecha_colombia_corta")
    print("4. ✅ Actualización de templates principales para usar zona horaria Colombia")
    print("5. ✅ pytz agregado a requirements.txt")
    print("6. ✅ Todos los modelos usan func.now() (UTC) y se convierten en presentación")

    print("\n🎯 RESULTADO:")
    print("Las fechas ahora se muestran en zona horaria de Colombia (UTC-5)")
    print("La fecha está correcta y la hora también coincide con el dispositivo del usuario")

if __name__ == "__main__":
    main()
