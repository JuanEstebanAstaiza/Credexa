"""
Router principal de la API
"""

from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.clientes import router as clientes_router
from app.api.prestamos import router as prestamos_router
from app.api.pagos import router as pagos_router
from app.api.reportes import router as reportes_router
from app.api.configuracion import router as configuracion_router
from app.api.socios import router as socios_router
from app.api.backup import router as backup_router
from app.api.documentos import router as documentos_router

api_router = APIRouter()

# Incluir routers de diferentes módulos
api_router.include_router(auth_router, tags=["autenticación"])
api_router.include_router(clientes_router, prefix="/clientes", tags=["clientes"])
api_router.include_router(prestamos_router, prefix="/prestamos", tags=["préstamos"])
api_router.include_router(pagos_router, prefix="/pagos", tags=["pagos"])
api_router.include_router(reportes_router, prefix="/reportes", tags=["reportes"])
api_router.include_router(configuracion_router, prefix="/configuracion", tags=["configuración"])
api_router.include_router(socios_router, prefix="/socios", tags=["socios"])
api_router.include_router(backup_router, prefix="/backup", tags=["backup"])
api_router.include_router(documentos_router, prefix="/documentos", tags=["documentos"])

# Aquí se agregarán los routers de otros módulos:
# api_router.include_router(reportes_router, prefix="/reportes", tags=["reportes"])
# api_router.include_router(pagos_router, prefix="/pagos", tags=["pagos"])
# api_router.include_router(reportes_router, prefix="/reportes", tags=["reportes"])
# api_router.include_router(configuracion_router, prefix="/configuracion", tags=["configuración"])
