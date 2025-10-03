#!/usr/bin/env python3
"""
Prueba del sistema de backup completo
"""
import os
import zipfile
from pathlib import Path
import requests

def test_backup_completo():
    print('🔍 PRUEBA DEL SISTEMA DE BACKUP COMPLETO')
    print('=' * 50)

    base_url = 'http://localhost:8000'

    # Login como admin
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_resp = requests.post(base_url + '/api/auth/login', data=login_data)

    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        print('✅ Login exitoso')

        # Verificar estadísticas iniciales
        stats_resp = requests.get(base_url + '/api/backup/estadisticas', headers=headers)
        print(f'✅ Estadísticas: {stats_resp.status_code}')

        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            print(f'   Backups completos: {stats.get("complete_backups", 0)}')
            print(f'   Backups DB: {stats.get("database_backups", 0)}')
            print(f'   Total: {stats.get("total_backups", 0)} backups')

        # Crear backup completo
        print('📦 Creando backup completo...')
        backup_resp = requests.post(base_url + '/api/backup/crear', headers=headers)

        if backup_resp.status_code == 200:
            backup_data = backup_resp.json()
            print(f'✅ Backup completo iniciado: {backup_data.get("filename", "Unknown")}')

            # Esperar un poco y verificar que se creó
            import time
            print('⏳ Esperando creación del backup...')
            time.sleep(3)

            # Verificar lista de backups
            list_resp = requests.get(base_url + '/api/backup/listar', headers=headers)
            if list_resp.status_code == 200:
                backups = list_resp.json()
                print(f'📋 Backups encontrados: {len(backups)}')

                # Buscar el backup más reciente
                if backups:
                    latest_backup = backups[0]  # Ya están ordenados por fecha
                    print(f'📦 Backup más reciente: {latest_backup["filename"]}')
                    print(f'   Tipo: {latest_backup.get("type", "desconocido")}')
                    print(f'   Tamaño: {latest_backup.get("size_human", "Unknown")}')
                    print(f'   Completo: {latest_backup.get("is_complete", False)}')

                    # Verificar que sea un archivo ZIP válido
                    backup_path = Path('backups') / latest_backup['filename']
                    if backup_path.exists() and latest_backup['filename'].endswith('.zip'):
                        try:
                            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                                file_list = zip_ref.namelist()
                                print(f'📂 Archivos en el ZIP: {len(file_list)}')

                                # Verificar contenido
                                has_db = any('instance/' in f and f.endswith('.db') for f in file_list)
                                has_docs = any('documentos/' in f for f in file_list)

                                print(f'   ✅ Base de datos: {"Sí" if has_db else "No"}')
                                print(f'   ✅ Documentos: {"Sí" if has_docs else "No"}')

                                if has_db and has_docs:
                                    print('🎉 ¡Backup completo validado exitosamente!')
                                else:
                                    print('⚠️ Backup incompleto')

                        except zipfile.BadZipFile:
                            print('❌ Archivo ZIP corrupto')
                    else:
                        print('❌ Backup no encontrado o no es ZIP')
                else:
                    print('❌ No se encontraron backups')
            else:
                print('❌ Error al listar backups')
        else:
            print(f'❌ Error al crear backup: {backup_resp.status_code}')
            print(f'   Respuesta: {backup_resp.text}')

    else:
        print('❌ Error de login')

if __name__ == "__main__":
    test_backup_completo()
