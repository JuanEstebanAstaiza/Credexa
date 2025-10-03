#!/usr/bin/env python3
"""
Prueba de persistencia de configuración de email
"""
import requests

def test_email_persistence():
    print('🔍 PRUEBA DE PERSISTENCIA DE CONFIGURACIÓN DE EMAIL')
    print('=' * 55)

    base_url = 'http://localhost:8000'

    # Login como admin
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_resp = requests.post(base_url + '/api/auth/login', data=login_data)

    if login_resp.status_code == 200:
        token = login_resp.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        print('✅ Login exitoso')

        # Verificar configuración inicial
        config_resp = requests.get(base_url + '/api/configuracion/email/config', headers=headers)
        print(f'✅ Obtener config inicial: {config_resp.status_code}')

        if config_resp.status_code == 200:
            initial_config = config_resp.json()
            print(f'   Estado inicial: {"Configurada" if initial_config["is_configured"] else "No configurada"}')

            # Configurar email (datos de prueba)
            test_config = {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_username": "test@example.com",
                "smtp_password": "test_password",
                "smtp_use_tls": True,
                "smtp_use_ssl": False,
                "email_from": "test@example.com",
                "email_from_name": "Credexa Test"
            }

            print('🧪 Configurando email de prueba...')
            config_post_resp = requests.post(
                base_url + '/api/configuracion/email/config',
                json=test_config,
                headers=headers
            )

            # Nota: Esto fallará porque las credenciales son falsas, pero debería guardar en BD
            print(f'✅ Configurar email: {config_post_resp.status_code}')

            # Verificar que se guardó en BD
            config_resp2 = requests.get(base_url + '/api/configuracion/email/config', headers=headers)
            print(f'✅ Verificar persistencia: {config_resp2.status_code}')

            if config_resp2.status_code == 200:
                saved_config = config_resp2.json()
                if saved_config.get("smtp_server") == "smtp.gmail.com":
                    print('🎉 ¡Configuración guardada correctamente en BD!')
                    print('   Servidor SMTP:', saved_config.get("smtp_server"))
                    print('   Puerto:', saved_config.get("smtp_port"))
                    print('   Usuario:', saved_config.get("smtp_username"))
                else:
                    print('❌ Configuración no se guardó correctamente')
            else:
                print('❌ Error al verificar configuración guardada')
        else:
            print('❌ Error al obtener configuración inicial')
    else:
        print('❌ Error de login')

if __name__ == "__main__":
    test_email_persistence()
