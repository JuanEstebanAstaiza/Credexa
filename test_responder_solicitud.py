#!/usr/bin/env python3
"""
Prueba del endpoint de respuesta a solicitudes de contraseña
"""
import requests

def test_responder_solicitud():
    print('🔍 PRUEBA DEL ENDPOINT DE RESPUESTA A SOLICITUDES')
    print('=' * 50)

    base_url = 'http://localhost:8000'

    # Login como admin
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_resp = requests.post(base_url + '/api/auth/login', data=login_data)

    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Obtener solicitudes
        solicitudes_resp = requests.get(base_url + '/api/auth/solicitudes-password', headers=headers)

        if solicitudes_resp.status_code == 200:
            data = solicitudes_resp.json()
            items = data.get('items', [])

            if items:
                solicitud_id = items[0]['id']
                print(f'✅ Probando responder solicitud ID: {solicitud_id}')

                # Responder solicitud (aprobar)
                respuesta_data = {
                    'estado': 'aprobada',
                    'comentarios_admin': 'Contraseña cambiada por solicitud del usuario'
                }

                responder_resp = requests.put(
                    base_url + f'/api/auth/solicitudes-password/{solicitud_id}',
                    json=respuesta_data,
                    headers=headers
                )

                print(f'✅ Respuesta endpoint: {responder_resp.status_code}')

                if responder_resp.status_code == 200:
                    result = responder_resp.json()
                    print(f'✅ Resultado: {result.get("message", "OK")}')
                    print('🎉 ¡El endpoint funciona correctamente!')
                else:
                    print(f'❌ Error: {responder_resp.text}')
            else:
                print('⚠️ No hay solicitudes para probar')
        else:
            print(f'❌ Error obteniendo solicitudes: {solicitudes_resp.text}')
    else:
        print('❌ Error de login')

if __name__ == "__main__":
    test_responder_solicitud()
