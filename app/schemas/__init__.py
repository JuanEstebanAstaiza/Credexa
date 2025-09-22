"""
Importar todos los esquemas
"""

from .user import (
    Rol, RolCreate, RolUpdate, RolBase,
    Usuario, UsuarioCreate, UsuarioUpdate, UsuarioBase,
    LoginRequest, Token, TokenData,
    PasswordResetRequest, PasswordReset
)
from .cliente import (
    Cliente, ClienteCreate, ClienteUpdate, ClienteBase,
    ClienteFiltro, ClientePaginado
)
from .prestamo import (
    Prestamo, PrestamoCreate, PrestamoUpdate, PrestamoBase,
    RefinanciacionCreate, PrestamoFiltro, PrestamoPaginado,
    EstadisticasPrestamo
)
from .pago import (
    Pago, PagoCreate, PagoUpdate, PagoBase,
    PagoFiltro, PagoPaginado, PagoRegistro
)
from .reporte import (
    ReportePago, ReporteMoroso, ReportePagoFiltro,
    ReporteMorosoFiltro, ReporteEstadistico
)
from .configuracion import (
    Configuracion, ConfiguracionCreate, ConfiguracionUpdate,
    ConfiguracionBase, ConfiguracionFiltro
)

__all__ = [
    "Rol", "RolCreate", "RolUpdate", "RolBase",
    "Usuario", "UsuarioCreate", "UsuarioUpdate", "UsuarioBase",
    "LoginRequest", "Token", "TokenData",
    "PasswordResetRequest", "PasswordReset",
    "Cliente", "ClienteCreate", "ClienteUpdate", "ClienteBase",
    "ClienteFiltro", "ClientePaginado",
    "Prestamo", "PrestamoCreate", "PrestamoUpdate", "PrestamoBase",
    "RefinanciacionCreate", "PrestamoFiltro", "PrestamoPaginado",
    "EstadisticasPrestamo",
    "Pago", "PagoCreate", "PagoUpdate", "PagoBase",
    "PagoFiltro", "PagoPaginado", "PagoRegistro",
    "ReportePago", "ReporteMoroso", "ReportePagoFiltro",
    "ReporteMorosoFiltro", "ReporteEstadistico",
    "Configuracion", "ConfiguracionCreate", "ConfiguracionUpdate",
    "ConfiguracionBase", "ConfiguracionFiltro"
]
