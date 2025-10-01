from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentoBase(BaseModel):
    nombre_original: str = Field(..., min_length=1, max_length=255, description="Nombre original del archivo")
    carpeta_id: int = Field(..., description="ID de la carpeta donde se almacena")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Descripción del documento")
    tipo_documento: Optional[str] = Field(None, max_length=50, description="Tipo de documento")

class DocumentoCreate(DocumentoBase):
    pass

class DocumentoUpdate(BaseModel):
    nombre_original: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=1000)
    tipo_documento: Optional[str] = Field(None, max_length=50)

class DocumentoResponse(DocumentoBase):
    id: int
    nombre_archivo: str
    ruta_archivo: str
    tipo_mime: Optional[str]
    tamano: int
    usuario_subio_id: int
    fecha_subida: datetime
    actualizado_en: Optional[datetime]
    tamano_human: str = ""  # Propiedad calculada

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Convertir desde ORM incluyendo propiedades calculadas"""
        data = super().from_orm(obj).__dict__
        # Agregar tamaño en formato humano
        tamano = data.get('tamano', 0)
        if tamano < 1024:
            data['tamano_human'] = f"{tamano} B"
        elif tamano < 1024 * 1024:
            data['tamano_human'] = f"{tamano / 1024:.1f} KB"
        else:
            data['tamano_human'] = f"{tamano / (1024 * 1024):.1f} MB"
        return cls(**data)
