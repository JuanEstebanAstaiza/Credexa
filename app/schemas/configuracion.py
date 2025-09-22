"""
Esquemas Pydantic para configuraciones del sistema
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ConfiguracionBase(BaseModel):
    clave: str = Field(..., max_length=100, description="Clave única de la configuración")
    valor: Optional[str] = Field(None, max_length=500, description="Valor de la configuración")
    tipo: str = Field("string", description="Tipo de dato: string, int, float, bool")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción de la configuración")
    categoria: Optional[str] = Field(None, max_length=100, description="Categoría de la configuración")


class ConfiguracionCreate(ConfiguracionBase):
    pass


class ConfiguracionUpdate(BaseModel):
    valor: Optional[str] = Field(None, max_length=500, description="Valor de la configuración")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción de la configuración")
    categoria: Optional[str] = Field(None, max_length=100, description="Categoría de la configuración")


class Configuracion(ConfiguracionBase):
    id: int
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True


class ConfiguracionFiltro(BaseModel):
    categoria: Optional[str] = None
    tipo: Optional[str] = None
