#!/usr/bin/env python3
"""
Verificar contraseña del admin
"""
import sqlite3
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import verify_password

# Conectar a la base de datos
conn = sqlite3.connect('instance/prestamos.db')
cursor = conn.cursor()

# Ver hash de contraseña del admin
cursor.execute('SELECT id, username, hashed_password FROM usuarios WHERE username = "admin"')
admin_data = cursor.fetchone()

if admin_data:
    user_id, username, hashed_pwd = admin_data
    print(f'👤 Admin encontrado - ID: {user_id}, Usuario: {username}')
    print(f'🔐 Hash de contraseña: {hashed_pwd[:50]}...')

    # Probar contraseñas comunes
    test_passwords = ['admin123', 'admin', '123456', 'password', 'test123456']

    for pwd in test_passwords:
        if verify_password(pwd, hashed_pwd):
            print(f'✅ Contraseña correcta: {pwd}')
            break
    else:
        print('❌ Contraseña no encontrada en lista de prueba')
        print('💡 Posiblemente cambió durante pruebas anteriores')

else:
    print('❌ Usuario admin no encontrado')

conn.close()
