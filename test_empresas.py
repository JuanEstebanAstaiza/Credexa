#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

try:
    from app.core.database import get_db
    from app.models import Empresa
    from sqlalchemy.orm import Session

    print("Testing database connection...")
    db = next(get_db())

    print("Testing query...")
    empresas = db.query(Empresa).limit(1).all()
    print(f"Found {len(empresas)} empresas")

    if empresas:
        emp = empresas[0]
        print(f"Empresa: {emp.nombre}, ID: {emp.id}")

        # Test serialization
        data = {
            'id': emp.id,
            'nombre': emp.nombre,
            'slug': emp.slug,
            'email': emp.email,
            'activo': emp.activo,
            'fecha_creacion': emp.fecha_creacion.isoformat() if emp.fecha_creacion else None,
        }
        print("Serialization test passed")

    db.close()
    print("Test completed successfully")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
