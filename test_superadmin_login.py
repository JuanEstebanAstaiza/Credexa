#!/usr/bin/env python3
"""
Script para probar el login del super-admin
"""

import requests
import json

def test_superadmin_login():
    """Probar login del super-admin"""

    print("Probando login del super-admin...")

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

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Login exitoso!")

            # Verificar la estructura de la respuesta
            if "user" in result:
                user = result["user"]
                print(f"Usuario: {user.get('username')}")
                print(f"Email: {user.get('email')}")
                print(f"Rol: {user.get('rol', {}).get('nombre') if user.get('rol') else 'Sin rol'}")
                print(f"Es super-admin: {user.get('is_super_admin', False)}")

                # Verificar que tenga el token
                if "access_token" in result:
                    print(f"Token generado: {result['access_token'][:50]}...")

                    # Probar acceder al dashboard de admin
                    admin_url = "http://localhost:8000/admin/dashboard"
                    headers = {"Cookie": f"access_token={result['access_token']}"}

                    admin_response = requests.get(admin_url, headers=headers, allow_redirects=False)
                    print(f"Dashboard admin - Status: {admin_response.status_code}")

                    if admin_response.status_code == 200:
                        print("Dashboard de super-admin accesible!")
                    else:
                        print(f"Error accediendo al dashboard: {admin_response.status_code}")
                        if admin_response.text:
                            print(f"Respuesta: {admin_response.text[:200]}...")

                else:
                    print("No se recibió token de acceso")
            else:
                print("Respuesta no contiene información del usuario")

        else:
            print(f"Login falló con código: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error.get('detail', 'Sin detalle')}")
            except:
                print(f"Respuesta: {response.text[:200]}")

    except Exception as e:
        print(f"Error en la petición: {e}")

if __name__ == "__main__":
    test_superadmin_login()
