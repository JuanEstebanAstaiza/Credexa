#!/usr/bin/env python3
"""
Script para probar el acceso completo al panel de super-admin
"""

import requests
import json

def test_admin_panels():
    """Probar acceso completo al panel de super-admin"""

    print("Probando acceso al panel de super-admin...")

    # URL del endpoint de login
    login_url = "http://localhost:8000/api/auth/login"

    # Credenciales del super-admin
    data = {
        "username": "superadmin",
        "password": "super123"
    }

    try:
        # Hacer la petición POST
        response = requests.post(login_url, data=data)

        print(f"Login - Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Login exitoso!")

            # Obtener token
            access_token = result.get("access_token")
            if access_token:
                # Probar acceso a diferentes paneles
                headers = {"Cookie": f"access_token={access_token}"}

                # Dashboard
                dashboard_response = requests.get("http://localhost:8000/admin/dashboard", headers=headers, allow_redirects=False)
                print(f"Dashboard - Status: {dashboard_response.status_code}")

                # Planes
                planes_response = requests.get("http://localhost:8000/admin/planes", headers=headers, allow_redirects=False)
                print(f"Planes - Status: {planes_response.status_code}")

                # Empresas
                empresas_response = requests.get("http://localhost:8000/admin/empresas", headers=headers, allow_redirects=False)
                print(f"Empresas - Status: {empresas_response.status_code}")

                # Suscripciones
                suscripciones_response = requests.get("http://localhost:8000/admin/suscripciones", headers=headers, allow_redirects=False)
                print(f"Suscripciones - Status: {suscripciones_response.status_code}")

                # Verificar que todos los paneles funcionan
                all_working = all([
                    dashboard_response.status_code == 200,
                    planes_response.status_code == 200,
                    empresas_response.status_code == 200,
                    suscripciones_response.status_code == 200
                ])

                if all_working:
                    print("\nTodas las paginas del panel de super-admin funcionan correctamente!")
                    print("El sistema SaaS multi-tenant esta completamente operativo.")
                else:
                    print("\nAlgunas paginas pueden tener problemas:")
                    print(f"- Dashboard: {dashboard_response.status_code}")
                    print(f"- Planes: {planes_response.status_code}")
                    print(f"- Empresas: {empresas_response.status_code}")
                    print(f"- Suscripciones: {suscripciones_response.status_code}")

            else:
                print("No se recibió token de acceso")
        else:
            print(f"Login falló: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error.get('detail', 'Sin detalle')}")
            except:
                print(f"Respuesta: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_admin_panels()
