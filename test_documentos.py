import requests

base_url = 'http://localhost:8000'

def test_documentos():
    # Crear sesión para mantener cookies/autenticación
    session = requests.Session()

    # Login como admin
    login_resp = session.post(base_url + '/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    if login_resp.status_code != 200:
        print('❌ Error de login')
        return

    token = login_resp.json()['access_token']
    headers = {'Authorization': 'Bearer ' + token}

    print('✅ Login exitoso')

    # Probar crear carpetas del mes
    print('\n📅 Creando carpetas del mes...')
    resp = session.post(base_url + '/api/documentos/automatizacion/crear-carpetas-mes', headers=headers)
    print(f'Estado: {resp.status_code}')
    if resp.status_code == 200:
        resultado = resp.json()
        print(f'✅ Carpetas creadas: {len(resultado.get("carpetas_creadas", []))}')
        if resultado.get('errores'):
            print(f'⚠️ Errores: {resultado["errores"]}')
    else:
        print(f'❌ Error: {resp.text}')

    # Probar listar carpetas
    print('\n📁 Listando carpetas...')
    resp = session.get(base_url + '/api/documentos/carpetas', headers=headers)
    print(f'Estado: {resp.status_code}')
    if resp.status_code == 200:
        carpetas = resp.json()
        print(f'✅ Encontradas {len(carpetas)} carpetas')
        if carpetas:
            print('Primeras 3 carpetas:')
            for carpeta in carpetas[:3]:
                print(f'  - {carpeta["nombre"]} ({carpeta["tipo"]})')
    else:
        print(f'❌ Error: {resp.text}')

    # Probar árbol de carpetas
    print('\n🌳 Probando árbol de carpetas...')
    resp = session.get(base_url + '/api/documentos/carpetas/arbol', headers=headers)
    print(f'Estado: {resp.status_code}')
    if resp.status_code == 200:
        arbol = resp.json()
        print(f'✅ Árbol cargado correctamente')
    else:
        print(f'❌ Error: {resp.text}')

    # Probar crear una carpeta manual
    print('\n📂 Creando carpeta manual...')
    carpeta_data = {
        "nombre": "Documentos_Prueba",
        "tipo": "manual",
        "descripcion": "Carpeta de prueba creada automáticamente"
    }
    resp = session.post(base_url + '/api/documentos/carpetas', json=carpeta_data, headers=headers)
    print(f'Estado: {resp.status_code}')
    if resp.status_code == 200:
        nueva_carpeta = resp.json()
        carpeta_id = nueva_carpeta['id']
        print(f'✅ Carpeta creada: {nueva_carpeta["nombre"]} (ID: {carpeta_id})')

        # Probar subir un documento pequeño
        print('\n📄 Subiendo documento de prueba...')
        with open(__file__, 'rb') as f:
            files = {'archivo': ('test_documentos.py', f, 'text/plain')}
            data = {
                'carpeta_id': str(carpeta_id),
                'tipo_documento': 'otro',
                'descripcion': 'Archivo de prueba para testing'
            }
            resp = session.post(base_url + '/api/documentos/documentos',
                               files=files, data=data)

        print(f'Estado: {resp.status_code}')
        if resp.status_code == 200:
            documento = resp.json()
            print(f'✅ Documento subido: {documento["nombre_original"]}')

            # Probar descargar el documento
            print('\n⬇️ Descargando documento...')
            resp = session.get(f'{base_url}/api/documentos/documentos/{documento["id"]}/descargar', headers=headers)
            print(f'Estado: {resp.status_code}')
            if resp.status_code == 200:
                print(f'✅ Documento descargado: {len(resp.content)} bytes')
            else:
                print(f'❌ Error al descargar: {resp.text}')
        else:
            print(f'❌ Error al subir: {resp.text}')
    else:
        print(f'❌ Error al crear carpeta: {resp.text}')

    print('\n🎯 Pruebas completadas!')

if __name__ == '__main__':
    test_documentos()
