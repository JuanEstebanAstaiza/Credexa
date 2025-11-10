#!/usr/bin/env python3
"""
Script completo para probar el dashboard del super-admin
"""

import requests
import json

def test_dashboard_complete():
    """Probar funcionalidad completa del dashboard"""

    print("Probando dashboard completo del super-admin...")
    print("=" * 50)

    # 1. Login
    print("1. Iniciando sesion como super-admin...")
    login_data = {
        "username": "superadmin",
        "password": "super123"
    }

    login_response = requests.post('http://localhost:8000/api/auth/login', data=login_data)

    if login_response.status_code != 200:
        print(f"Error en login: {login_response.status_code}")
        print(f"Respuesta: {login_response.text}")
        return False

    token = login_response.json()['access_token']
    headers = {'Cookie': f'access_token={token}'}
    print("Login exitoso")

    # 2. Acceso al dashboard
    print("\n2. Probando acceso al dashboard...")
    dashboard_response = requests.get('http://localhost:8000/admin/dashboard', headers=headers, allow_redirects=False)

    if dashboard_response.status_code != 200:
        print(f"Error en dashboard: {dashboard_response.status_code}")
        return False

    print("Dashboard accesible")

    # 3. API de empresas
    print("\n3. Probando API de empresas...")
    empresas_response = requests.get('http://localhost:8000/api/empresas/', headers=headers, allow_redirects=False)

    if empresas_response.status_code != 200:
        print(f"Error en API empresas: {empresas_response.status_code}")
        print(f"Respuesta: {empresas_response.text}")
        return False

    empresas = empresas_response.json()
    print(f"API empresas funciona - {len(empresas)} empresa(s) encontrada(s)")

    # 4. API de planes
    print("\n4. Probando API de planes...")
    planes_response = requests.get('http://localhost:8000/api/admin/planes-suscripcion/', headers=headers, allow_redirects=False)

    if planes_response.status_code != 200:
        print(f"Error en API planes: {planes_response.status_code}")
        return False

    print("API planes funciona")

    # 5. API de suscripciones
    print("\n5. Probando API de suscripciones...")
    suscripciones_response = requests.get('http://localhost:8000/api/admin/suscripciones/', headers=headers, allow_redirects=False)

    if suscripciones_response.status_code != 200:
        print(f"Error en API suscripciones: {suscripciones_response.status_code}")
        return False

    print("API suscripciones funciona")

    # 6. Estadísticas de suscripciones
    print("\n6. Probando estadisticas de suscripciones...")
    stats_response = requests.get('http://localhost:8000/api/admin/suscripciones/stats/general', headers=headers, allow_redirects=False)

    if stats_response.status_code != 200:
        print(f"Error en estadisticas: {stats_response.status_code}")
        return False

    stats = stats_response.json()
    print(f"Estadisticas obtenidas:")
    print(f"   - Suscripciones activas: {stats.get('suscripciones_activas', 0)}")
    print(f"   - Ingresos mensuales: ${stats.get('ingresos_mensuales_actuales', 0):,.0f}")

    print("\n" + "=" * 50)
    print("TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    print("El dashboard del super-admin esta completamente funcional.")
    print("=" * 50)

    return True

if __name__ == "__main__":
    test_dashboard_complete()
