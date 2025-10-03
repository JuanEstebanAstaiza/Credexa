#!/usr/bin/env python3
"""
Verificar bases de datos y usuarios
"""
import sqlite3

# Verificar ambas bases de datos
dbs = ['instance/contabilidad_conjunto.db', 'instance/prestamos.db']

for db_path in dbs:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ver tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f'📁 {db_path}:')
        print(f'  Tablas: {[t[0] for t in tables]}')

        # Si tiene tabla usuarios, mostrar usuarios
        if 'usuarios' in [t[0] for t in tables]:
            cursor.execute('SELECT id, username, nombre_completo, rol_id FROM usuarios')
            users = cursor.fetchall()
            print(f'  👥 Usuarios: {len(users)}')
            for user in users[:3]:  # Mostrar máximo 3
                user_id, username, nombre, rol_id = user
                rol = 'Admin' if rol_id == 1 else 'Digitador'
                print(f'    ID: {user_id}, Usuario: {username}, Nombre: {nombre}, Rol: {rol}')

        conn.close()
        print()
    except Exception as e:
        print(f'❌ Error con {db_path}: {e}')
        print()
