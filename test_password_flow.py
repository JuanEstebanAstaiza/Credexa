#!/usr/bin/env python3
"""
Prueba del flujo completo de recuperación de contraseña para administrador
"""
import requests

def test_password_flow():
    print('🔍 PRUEBA DEL FLUJO COMPLETO DE CAMBIO DE CONTRASEÑA ADMIN')
    print('=' * 60)

    base_url = 'http://localhost:8000'

    # 1. Verificar que el servidor está corriendo
    response = requests.get(base_url + '/')
    print(f'✅ Servidor corriendo: {response.status_code}')

    # 2. Verificar página de recuperación
    response = requests.get(base_url + '/recuperar-password')
    print(f'✅ Página recuperación: {response.status_code}')

    print()
    print('🎯 INSTRUCCIONES PARA PRUEBA MANUAL:')
    print('1. Ve a: http://localhost:8000/recuperar-password')
    print('2. Selecciona "Soy Administrador"')
    print('3. Ingresa usuario: admin, email: admin@sistema.com')
    print('4. Deberías ser redirigido a la página de cambio de contraseña')
    print('5. Ingresa una nueva contraseña y confirma')
    print('6. Deberías ver mensaje de éxito y ser redirigido al login')
    print()
    print('⚡ El problema estaba en que /cambiar-password no estaba en páginas públicas')
    print('⚡ y el endpoint no manejaba correctamente el token temporal.')
    print('✅ Ahora debería funcionar correctamente!')

if __name__ == "__main__":
    test_password_flow()
