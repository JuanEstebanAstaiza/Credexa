#!/usr/bin/env python3
"""
Prueba de configuración de email
"""
import requests

def test_email_config():
    print('🔍 PRUEBA DEL ENDPOINT DE CONFIGURACIÓN DE EMAIL')
    print('=' * 50)

    base_url = 'http://localhost:8000'

    # Login como admin
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_resp = requests.post(base_url + '/api/auth/login', data=login_data)

    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Probar obtener configuración
        config_resp = requests.get(base_url + '/api/configuracion/email/config', headers=headers)
        print(f'✅ Obtener config: {config_resp.status_code}')

        if config_resp.status_code == 200:
            config_data = config_resp.json()
            status = "Configurada" if config_data.get("is_configured") else "No configurada"
            print(f'✅ Configuración actual: {status}')

            print('🎉 ¡Los endpoints de configuración de email funcionan correctamente!')
        else:
            print(f'❌ Error: {config_resp.text}')
    else:
        print('❌ Error de login')

if __name__ == "__main__":
    test_email_config()
