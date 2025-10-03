"""
Configuración de la aplicación
"""

import os
from typing import List
import secrets
from pathlib import Path
import pytz

class Settings:
    """Configuración de la aplicación"""

    # Base de datos
    DATABASE_URL: str = "sqlite:///./instance/prestamos.db"

    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Aplicación
    APP_NAME: str = "Credexa"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Zona horaria (Colombia)
    TIMEZONE: str = "America/Bogota"

    # Configuración de empresa (por defecto)
    EMPRESA_NOMBRE: str = "Credexa"
    EMPRESA_DIRECCION: str = ""
    EMPRESA_TELEFONO: str = ""
    EMPRESA_EMAIL: str = ""

    # Configuración de préstamos (por defecto)
    TASA_INTERES_POR_DEFECTO: float = 2.5  # Porcentaje mensual
    DIAS_GRACIA_POR_DEFECTO: int = 5
    DIAS_MORA_MAXIMOS: int = 90

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    class Config:
        env_file = ".env"

# Instancia de configuración
settings = Settings()
