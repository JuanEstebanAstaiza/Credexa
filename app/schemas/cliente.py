"""
Esquemas Pydantic para Cliente
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
import re

# Esquemas base
class ClienteBase(BaseModel):
    nombre_completo: str
    cedula: str
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    fecha_nacimiento: Optional[datetime] = None
    ocupacion: Optional[str] = None
    ingresos_mensuales: Optional[int] = None
    referencias_personales: Optional[str] = None
    activo: Optional[int] = 1
    notas: Optional[str] = None

    @validator('cedula')
    def validar_cedula(cls, v):
        """Validar formato de cédula colombiana (solo números, 6-10 dígitos)"""
        if not v:
            raise ValueError('La cédula es requerida')

        # Remover puntos y espacios
        cedula_limpia = re.sub(r'[.\s]', '', v)

        if not cedula_limpia.isdigit():
            raise ValueError('La cédula debe contener solo números')

        if len(cedula_limpia) < 6 or len(cedula_limpia) > 10:
            raise ValueError('La cédula debe tener entre 6 y 10 dígitos')

        return cedula_limpia

    @validator('telefono')
    def validar_telefono(cls, v):
        """Validar formato de teléfono colombiano"""
        if v:
            # Remover espacios, guiones y paréntesis, pero mantener el +
            telefono_limpio = re.sub(r'[()\s\-]', '', v)

            # Verificar si tiene prefijo internacional +57
            if telefono_limpio.startswith('+57'):
                # Para formato internacional: +57 seguido de 10 dígitos
                numero_sin_prefijo = telefono_limpio[3:]  # Remover +57
                if not numero_sin_prefijo.isdigit():
                    raise ValueError('El teléfono debe contener solo números después del prefijo +57')
                if len(numero_sin_prefijo) != 10:
                    raise ValueError('El teléfono con prefijo +57 debe tener exactamente 10 dígitos')
            else:
                # Para formato local: solo números
                if not telefono_limpio.isdigit():
                    raise ValueError('El teléfono debe contener solo números')

                if len(telefono_limpio) < 7 or len(telefono_limpio) > 10:
                    raise ValueError('El teléfono debe tener entre 7 y 10 dígitos')

        return v

    @validator('ingresos_mensuales')
    def validar_ingresos(cls, v):
        """Validar que los ingresos sean positivos"""
        if v is not None and v < 0:
            raise ValueError('Los ingresos mensuales no pueden ser negativos')
        return v

# Esquemas para crear
class ClienteCreate(ClienteBase):
    pass

# Esquemas para actualizar
class ClienteUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    fecha_nacimiento: Optional[datetime] = None
    ocupacion: Optional[str] = None
    ingresos_mensuales: Optional[int] = None
    referencias_personales: Optional[str] = None
    activo: Optional[int] = None
    notas: Optional[str] = None

# Esquemas para respuesta
class Cliente(ClienteBase):
    id: int
    creado_en: datetime
    actualizado_en: Optional[datetime]

    class Config:
        from_attributes = True

# Esquemas para búsqueda y filtros
class ClienteFiltro(BaseModel):
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    activo: Optional[int] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None

class ClientePaginado(BaseModel):
    items: list[Cliente]
    total: int
    pagina: int
    por_pagina: int
    paginas_totales: int
