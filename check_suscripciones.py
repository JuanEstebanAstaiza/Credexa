from app.core.database import get_db
from app.models.suscripcion import Suscripcion

db = next(get_db())

# Verificar todas las suscripciones
suscripciones = db.query(Suscripcion).all()
print('Todas las suscripciones en DB:')
for s in suscripciones:
    print(f'ID: {s.id}, Empresa: {s.empresa_id}, Estado: {s.estado}, Tipo: {s.tipo}')

# Verificar cuáles son consideradas activas por la query
suscripciones_activas = db.query(Suscripcion).filter(
    Suscripcion.estado == 'activa'
).all()
print(f'\nSuscripciones con estado == "activa": {len(suscripciones_activas)}')

db.close()
