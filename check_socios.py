import sqlite3

conn = sqlite3.connect('instance/prestamos.db')
cursor = conn.cursor()

# Verificar tabla pagos_socio
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pagos_socio'")
table_exists = cursor.fetchone()

if table_exists:
    print('✅ Tabla pagos_socio existe')

    cursor.execute('SELECT COUNT(*) FROM pagos_socio')
    total_pagos = cursor.fetchone()[0]
    print(f'Total pagos socios: {total_pagos}')

    if total_pagos > 0:
        cursor.execute('SELECT tipo, COUNT(*), SUM(monto) FROM pagos_socio GROUP BY tipo')
        tipos = cursor.fetchall()
        print('Tipos encontrados:')
        for tipo, count, total in tipos:
            print(f'  {tipo}: {count} pagos, ${total or 0}')
    else:
        print('❌ No hay pagos registrados')

        cursor.execute('SELECT COUNT(*) FROM socios')
        total_socios = cursor.fetchone()[0]
        print(f'Total socios: {total_socios}')

else:
    print('❌ Tabla pagos_socio no existe')

conn.close()
