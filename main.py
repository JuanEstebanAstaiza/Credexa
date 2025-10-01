"""
Credexa - Sistema de Gestión Financiera
Plataforma completa para gestión de préstamos y finanzas
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from app.core.config import settings
from app.core.database import engine, get_db, create_tables
from app.api.api import api_router
from app.core.security import get_current_user, get_current_user_optional, get_current_admin_user
from app.models.user import Usuario

# Crear las tablas de la base de datos
create_tables()

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión de Préstamos",
    description="Aplicación web para gestión de préstamos de pequeña empresa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Incluir routers
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, current_user = Depends(get_current_user_optional)):
    """Página principal - redirige al login si no está autenticado"""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user = Depends(get_current_user_optional)):
    """Página de login"""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "title": "Iniciar Sesión"
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user = Depends(get_current_user_optional)):
    """Dashboard principal"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "user": current_user
    })

@app.get("/clientes")
async def clientes_redirect(request: Request, current_user = Depends(get_current_user_optional)):
    """Redireccionar a lista de clientes"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/clientes/lista", status_code=302)

@app.get("/clientes/lista", response_class=HTMLResponse)
async def clientes_lista(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de listado de clientes"""
    return templates.TemplateResponse("clientes/lista.html", {
        "request": request,
        "title": "Lista de Clientes",
        "user": current_user
    })

@app.get("/clientes/nuevo", response_class=HTMLResponse)
async def clientes_nuevo(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de creación de cliente"""
    return templates.TemplateResponse("clientes/formulario.html", {
        "request": request,
        "title": "Nuevo Cliente",
        "user": current_user,
        "modo": "crear"
    })

@app.get("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
async def clientes_editar(
    cliente_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de edición de cliente"""
    from app.models.cliente import Cliente
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )

    return templates.TemplateResponse("clientes/formulario.html", {
        "request": request,
        "title": f"Editar Cliente: {cliente.nombre_completo}",
        "user": current_user,
        "modo": "editar",
        "cliente": cliente
    })

@app.get("/prestamos")
async def prestamos_redirect(request: Request, current_user = Depends(get_current_user_optional)):
    """Redireccionar a lista de préstamos"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/prestamos/lista", status_code=302)

@app.get("/prestamos/lista", response_class=HTMLResponse)
async def prestamos_lista(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de listado de préstamos"""
    return templates.TemplateResponse("prestamos/lista.html", {
        "request": request,
        "title": "Lista de Créditos",
        "user": current_user
    })

@app.get("/prestamos/nuevo", response_class=HTMLResponse)
async def prestamos_nuevo(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de creación de préstamo"""
    from app.models.cliente import Cliente
    from app.models.socio import Socio

    # Obtener lista de clientes activos para el select
    clientes = db.query(Cliente).filter(Cliente.activo == 1).order_by(Cliente.nombre_completo).all()

    # Obtener lista de socios activos con capital disponible
    socios = db.query(Socio).filter(
        Socio.activo == True,
        Socio.capital_actual > 0
    ).order_by(Socio.nombre_completo).all()

    return templates.TemplateResponse("prestamos/formulario.html", {
        "request": request,
        "title": "Nuevo Préstamo",
        "user": current_user,
        "modo": "crear",
        "clientes": clientes,
        "socios": socios
    })

@app.get("/prestamos/{prestamo_id}/detalle", response_class=HTMLResponse)
async def prestamos_detalle(
    prestamo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de detalle de préstamo"""
    from app.models.prestamo import Prestamo
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    # Las propiedades calculadas se manejan en el template

    return templates.TemplateResponse("prestamos/detalle.html", {
        "request": request,
        "title": f"Préstamo #{prestamo.id}",
        "user": current_user,
        "prestamo": prestamo
    })

@app.get("/prestamos/{prestamo_id}/refinanciar", response_class=HTMLResponse)
async def refinanciar_prestamo(
    prestamo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de refinanciación de préstamo"""
    from app.models.prestamo import Prestamo
    prestamo = db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado",
        )

    # Verificar que el préstamo pueda ser refinanciado
    if prestamo.estado == "pagado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede refinanciar un préstamo pagado"
        )

    if prestamo.saldo_pendiente <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El préstamo no tiene saldo pendiente"
        )

    return templates.TemplateResponse("prestamos/refinanciar.html", {
        "request": request,
        "title": f"Refinanciar Crédito #{prestamo.id}",
        "user": current_user,
        "prestamo": prestamo
    })

@app.get("/pagos")
async def pagos_redirect(request: Request, current_user = Depends(get_current_user_optional)):
    """Redireccionar a lista de pagos"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/pagos/lista", status_code=302)

@app.get("/pagos/lista", response_class=HTMLResponse)
async def pagos_lista(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de listado de pagos"""
    return templates.TemplateResponse("pagos/lista.html", {
        "request": request,
        "title": "Lista de Pagos",
        "user": current_user
    })

@app.get("/pagos/registrar", response_class=HTMLResponse)
async def pagos_registrar(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de registro de pago"""
    from app.models.prestamo import Prestamo
    # Obtener préstamos activos para el select
    prestamos = db.query(Prestamo).filter(Prestamo.estado == "activo").order_by(Prestamo.fecha_inicio.desc()).all()

    return templates.TemplateResponse("pagos/registrar.html", {
        "request": request,
        "title": "Registrar Pago",
        "user": current_user,
        "prestamos": prestamos
    })

@app.get("/pagos/{pago_id}/detalle", response_class=HTMLResponse)
async def pagos_detalle(
    pago_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de detalle de pago"""
    from app.models.pago import Pago
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado",
        )

    return templates.TemplateResponse("pagos/detalle.html", {
        "request": request,
        "title": f"Pago #{pago.id}",
        "user": current_user,
        "pago": pago
    })

# Rutas de Reportes
@app.get("/reportes", response_class=HTMLResponse)
async def reportes_index(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página principal de reportes"""
    return templates.TemplateResponse("reportes/index.html", {
        "request": request,
        "title": "Reportes del Sistema",
        "user": current_user
    })

@app.get("/reportes/pagos", response_class=HTMLResponse)
async def reportes_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de reporte de pagos por fecha"""
    return templates.TemplateResponse("reportes/pagos.html", {
        "request": request,
        "title": "Reporte de Pagos",
        "user": current_user
    })

@app.get("/reportes/morosos", response_class=HTMLResponse)
async def reportes_morosos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de reporte de clientes morosos"""
    return templates.TemplateResponse("reportes/morosos.html", {
        "request": request,
        "title": "Clientes Morosos",
        "user": current_user
    })

# Rutas de Configuración
@app.get("/configuracion", response_class=HTMLResponse)
async def configuracion_index(
    request: Request,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página principal de configuración del sistema"""
    return templates.TemplateResponse("configuracion/index.html", {
        "request": request,
        "title": "Configuración del Sistema",
        "user": current_user
    })

@app.get("/configuracion/usuarios", response_class=HTMLResponse)
async def configuracion_usuarios(
    request: Request,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de gestión de usuarios"""
    return templates.TemplateResponse("configuracion/usuarios.html", {
        "request": request,
        "title": "Gestión de Usuarios",
        "user": current_user
    })

@app.get("/configuracion/sistema", response_class=HTMLResponse)
async def configuracion_sistema(
    request: Request,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de configuración del sistema"""
    return templates.TemplateResponse("configuracion/sistema.html", {
        "request": request,
        "title": "Configuración del Sistema",
        "user": current_user
    })

# Rutas de Socios
@app.get("/socios")
async def socios_redirect(request: Request, current_user = Depends(get_current_user_optional)):
    """Redireccionar a lista de socios"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/socios/lista", status_code=302)

@app.get("/socios/lista", response_class=HTMLResponse)
async def socios_lista(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de listado de socios"""
    return templates.TemplateResponse("socios/lista.html", {
        "request": request,
        "title": "Lista de Socios",
        "user": current_user
    })

@app.get("/socios/crear", response_class=HTMLResponse)
async def socios_crear(
    request: Request,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de creación de socio"""
    return templates.TemplateResponse("socios/crear.html", {
        "request": request,
        "title": "Nuevo Socio",
        "user": current_user
    })

@app.get("/socios/{socio_id}/editar", response_class=HTMLResponse)
async def socios_editar(
    socio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de edición de socio"""
    from app.models.socio import Socio
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado",
        )

    return templates.TemplateResponse("socios/editar.html", {
        "request": request,
        "title": f"Editar Socio: {socio.nombre_completo}",
        "user": current_user,
        "socio": socio
    })

@app.get("/socios/{socio_id}/detalle", response_class=HTMLResponse)
async def socios_detalle(
    socio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Página de detalle de socio"""
    from app.models.socio import Socio
    socio = db.query(Socio).filter(Socio.id == socio_id).first()
    if not socio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Socio no encontrado",
        )

    return templates.TemplateResponse("socios/detalle.html", {
        "request": request,
        "title": f"Socio: {socio.nombre_completo}",
        "user": current_user,
        "socio": socio
    })

@app.get("/socios/pagos", response_class=HTMLResponse)
async def socios_pagos(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de pagos de socios"""
    return templates.TemplateResponse("socios/pagos.html", {
        "request": request,
        "title": "Pagos de Socios",
        "user": current_user
    })

@app.get("/socios/deudas", response_class=HTMLResponse)
async def socios_deudas(
    request: Request,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de deudas de la empresa con socios"""
    return templates.TemplateResponse("socios/deudas.html", {
        "request": request,
        "title": "Deudas con Socios",
        "user": current_user
    })

@app.get("/socios/retiro", response_class=HTMLResponse)
async def socios_retiro(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de gestión de retiros de socios (solo administradores)"""
    from app.models.socio import Socio

    # Obtener todos los socios activos para selección
    socios = db.query(Socio).filter(Socio.activo == True).order_by(Socio.nombre_completo).all()

    if not socios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay socios registrados"
        )

    return templates.TemplateResponse("socios/retiro.html", {
        "request": request,
        "title": "Gestión de Retiros de Socios",
        "user": current_user,
        "socios": socios,
        "socio": socios[0] if socios else None  # Socio por defecto para compatibilidad
    })

# Ruta de Backup
@app.get("/backup", response_class=HTMLResponse)
async def backup_index(
    request: Request,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """Página de gestión de backups"""
    return templates.TemplateResponse("backup/index.html", {
        "request": request,
        "title": "Gestión de Backups",
        "user": current_user
    })

# Rutas de Documentos
@app.get("/documentos", response_class=HTMLResponse)
async def documentos_index(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página principal de gestión de documentos"""
    # Convertir usuario a diccionario serializable
    user_dict = {
        "id": current_user.id,
        "nombre_completo": current_user.nombre_completo,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "is_digitador": current_user.is_digitador
    }

    return templates.TemplateResponse("documentos/index.html", {
        "request": request,
        "title": "Gestión de Documentos",
        "user": user_dict,
        "config": settings
    })

# Ruta de Perfil de Usuario
@app.get("/perfil", response_class=HTMLResponse)
async def perfil_usuario(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Página de perfil del usuario"""
    return templates.TemplateResponse("perfil.html", {
        "request": request,
        "title": "Mi Perfil",
        "user": current_user
    })

@app.get("/logout")
async def logout():
    """Cerrar sesión - redirige al login"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
