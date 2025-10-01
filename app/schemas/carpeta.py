from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CarpetaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre de la carpeta")
    tipo: str = Field(..., pattern=r'^(mes|socio|cliente|prestamo|manual)$', description="Tipo de carpeta")
    parent_id: Optional[int] = Field(None, description="ID de la carpeta padre")
    entidad_id: Optional[int] = Field(None, description="ID del cliente o socio relacionado")
    entidad_tipo: Optional[str] = Field(None, pattern=r'^(cliente|socio)$', description="Tipo de entidad")
    prestamo_id: Optional[int] = Field(None, description="ID del préstamo relacionado")
    es_automatica: bool = Field(False, description="Si la carpeta fue creada automáticamente")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Descripción de la carpeta")

class CarpetaCreate(CarpetaBase):
    pass

class CarpetaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=1000)

class CarpetaResponse(CarpetaBase):
    id: int
    ruta_completa: str
    creada_por: Optional[int]
    creado_en: datetime
    actualizado_en: Optional[datetime]
    subcarpetas: List['CarpetaResponse'] = []
    documentos_count: int = 0

    class Config:
        from_attributes = True

class CarpetaTreeResponse(BaseModel):
    id: int
    nombre: str
    ruta_completa: str
    tipo: str
    subcarpetas: List['CarpetaTreeResponse'] = []
    documentos_count: int = 0

    class Config:
        from_attributes = True
