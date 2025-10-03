#!/usr/bin/env python3
"""
Prueba del endpoint de solicitudes de contraseña
"""
import requests

def test_solicitudes():
    print('🔍 PRUEBA DEL ENDPOINT DE SOLICITUDES DE CONTRASEÑA')
    print('=' * 50)

    base_url = 'http://localhost:8000'

    # Login como admin
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_resp = requests.post(base_url + '/api/auth/login', data=login_data)

    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Probar endpoint de solicitudes de contraseña
        solicitudes_resp = requests.get(base_url + '/api/auth/solicitudes-password', headers=headers)
        print(f'✅ Endpoint solicitudes: {solicitudes_resp.status_code}')

        if solicitudes_resp.status_code == 200:
            data = solicitudes_resp.json()
            print(f'✅ Solicitudes encontradas: {len(data.get("items", []))}')
            print('🎉 ¡El endpoint funciona correctamente!')
        else:
            print(f'❌ Error: {solicitudes_resp.text}')
    else:
        print('❌ Error de login')

if __name__ == "__main__":
    test_solicitudes()
