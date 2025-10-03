"""
Importar todos los modelos
"""

from .user import Usuario, Rol
from .cliente import Cliente
from .prestamo import Prestamo
from .pago import Pago
from .socio import Socio
from .pago_socio import PagoSocio
from .carpeta import Carpeta
from .documento import Documento
from .configuracion import Configuracion
from .solicitud_password import SolicitudPassword

__all__ = [
    "Usuario", "Rol", "Cliente", "Prestamo", "Pago",
    "Socio", "PagoSocio", "Carpeta", "Documento", "Configuracion",
    "SolicitudPassword"
]
