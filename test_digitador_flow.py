#!/usr/bin/env python3
"""
Prueba del flujo completo para digitadores solicitando cambio de contraseña
"""
import requests

def test_digitador_flow():
    print('🔍 PRUEBA DEL FLUJO COMPLETO PARA DIGITADORES')
    print('=' * 60)

    base_url = 'http://localhost:8000'

    # 1. Verificar página de recuperación
    response = requests.get(base_url + '/recuperar-password')
    print(f'✅ Página recuperación: {response.status_code}')

    if 'Solicitar Cambio de Contraseña' in response.text:
        print('✅ Nueva opción para digitadores presente')
    else:
        print('❌ Nueva opción faltante')

    # 2. Probar solicitud de cambio de contraseña
    print()
    print('🧪 PROBANDO SOLICITUD DE CAMBIO:')
    solicitud_data = {
        'username': 'digitador1',
        'email': 'digitador1@sistema.com',
        'motivo': 'Olvidé mi contraseña de prueba'
    }

    try:
        solicitud_resp = requests.post(base_url + '/api/auth/solicitar-cambio-password-publico',
                                     json=solicitud_data)
        print(f'✅ Endpoint solicitud: {solicitud_resp.status_code}')

        if solicitud_resp.status_code == 200:
            result = solicitud_resp.json()
            print(f'✅ Respuesta: {result.get("message", "OK")}')
        else:
            print(f'❌ Error: {solicitud_resp.text}')

    except Exception as e:
        print(f'❌ Error de conexión: {e}')

    print()
    print('🎯 INSTRUCCIONES PARA PRUEBA MANUAL:')
    print('1. Ve a: http://localhost:8000/recuperar-password')
    print('2. Haz clic en "Soy Digitador"')
    print('3. Completa el formulario con:')
    print('   - Usuario: digitador1')
    print('   - Email: digitador1@sistema.com')
    print('   - Motivo: Olvidé mi contraseña')
    print('4. Deberías ver mensaje de éxito')
    print('5. El administrador podrá ver la solicitud en la gestión de contraseñas')

if __name__ == "__main__":
    test_digitador_flow()
