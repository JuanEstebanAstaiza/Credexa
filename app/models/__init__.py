"""
Importar todos los modelos
"""

from .user import Usuario, Rol
from .cliente import Cliente
from .prestamo import Prestamo
from .pago import Pago
from .configuracion import Configuracion

__all__ = ["Usuario", "Rol", "Cliente", "Prestamo", "Pago", "Configuracion"]
