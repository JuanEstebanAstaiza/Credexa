import requests

base_url = 'http://localhost:8000'

def test_completo_documentos():
    # Crear sesión
    session = requests.Session()

    # Login
    login_resp = session.post(base_url + '/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    if login_resp.status_code != 200:
        print('❌ Error de login')
        return

    token = login_resp.json()['access_token']
    headers = {'Authorization': 'Bearer ' + token}

    print('✅ Login exitoso')

    # 1. Crear carpetas del mes
    print('\n📅 Creando carpetas del mes...')
    resp = requests.post(base_url + '/api/documentos/automatizacion/crear-carpetas-mes', headers=headers)
    if resp.status_code == 200:
        resultado = resp.json()
        carpetas_creadas = len(resultado.get("carpetas_creadas", []))
        print(f'✅ Carpetas creadas: {carpetas_creadas}')
        if resultado.get('errores'):
            print(f'⚠️ Errores: {resultado["errores"]}')
    else:
        print(f'❌ Error: {resp.status_code}')

    # 2. Listar carpetas
    print('\n📁 Listando carpetas...')
    resp = requests.get(base_url + '/api/documentos/carpetas', headers=headers)
    if resp.status_code == 200:
        carpetas = resp.json()
        print(f'✅ Encontradas {len(carpetas)} carpetas')

        # Buscar una carpeta de cliente
        carpeta_cliente = None
        for carpeta in carpetas:
            if carpeta['tipo'] == 'cliente':
                carpeta_cliente = carpeta
                break

        if carpeta_cliente:
            print(f'📂 Usando carpeta cliente: {carpeta_cliente["nombre"]} (ID: {carpeta_cliente["id"]})')

            # 3. Subir documento
            print('\n📄 Subiendo documento de prueba...')
            with open(__file__, 'rb') as f:
                files = {'archivo': ('test_completo.py', f, 'text/plain')}
                data = {
                    'carpeta_id': str(carpeta_cliente['id']),
                    'tipo_documento': 'otro',
                    'descripcion': 'Archivo de prueba del test completo'
                }
                resp = requests.post(base_url + '/api/documentos/documentos', files=files, data=data, headers=headers)

            if resp.status_code == 200:
                documento = resp.json()
                print(f'✅ Documento subido: {documento["nombre_original"]}')

                # 4. Descargar documento
                print('\n⬇️ Descargando documento...')
                resp = requests.get(f'{base_url}/api/documentos/documentos/{documento["id"]}/descargar', headers=headers)
                if resp.status_code == 200:
                    print(f'✅ Documento descargado: {len(resp.content)} bytes')
                else:
                    print(f'❌ Error al descargar: {resp.status_code}')

                # 5. Listar documentos en la carpeta
                print('\n📋 Listando documentos en carpeta...')
                resp = requests.get(f'{base_url}/api/documentos/documentos?carpeta_id={carpeta_cliente["id"]}', headers=headers)
                if resp.status_code == 200:
                    documentos = resp.json()
                    print(f'✅ Documentos en carpeta: {len(documentos)}')
                else:
                    print(f'❌ Error al listar: {resp.status_code}')
            else:
                print(f'❌ Error al subir: {resp.status_code} - {resp.text}')
        else:
            print('❌ No se encontró carpeta de cliente')
    else:
        print(f'❌ Error al listar: {resp.status_code}')

    # 6. Verificar estructura
    print('\n🔍 Verificando estructura...')
    resp = requests.post(base_url + '/api/documentos/automatizacion/verificar-estructura', headers=headers)
    if resp.status_code == 200:
        resultado = resp.json()
        carpetas_verificadas = resultado.get("carpetas_verificadas", 0)
        print(f'✅ Verificación completada: {carpetas_verificadas} carpetas')
    else:
        print(f'❌ Error en verificación: {resp.status_code}')

    print('\n🎯 Test completo finalizado!')

if __name__ == '__main__':
    test_completo_documentos()
