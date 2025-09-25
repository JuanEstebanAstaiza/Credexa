import requests

base_url = 'http://localhost:8000'

# Login como admin
login_resp = requests.post(base_url + '/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
if login_resp.status_code == 200:
    token = login_resp.json()['access_token']
    headers = {'Authorization': 'Bearer ' + token}

    print('Verificando lista de backups...')
    resp = requests.get(base_url + '/api/backup/listar', headers=headers)
    if resp.status_code == 200:
        backups = resp.json()
        print(f'Encontrados {len(backups)} backups:')
        for backup in backups:
            print(f'  - {backup["filename"]} ({backup["size_human"]})')
    else:
        print(f'Error: {resp.status_code}')
else:
    print('Error de login')
