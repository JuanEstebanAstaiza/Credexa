from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Documento(Base):
    __tablename__ = "documentos"
    id = Column(Integer, primary_key=True, index=True)
    nombre_original = Column(String(255), nullable=False)
    nombre_archivo = Column(String(255), nullable=False, index=True)  # Nombre en el sistema de archivos
    ruta_archivo = Column(String(1000), nullable=False)  # Ruta completa del archivo
    tipo_mime = Column(String(100), nullable=True)
    tamano = Column(BigInteger, nullable=False)  # Tamaño en bytes
    carpeta_id = Column(Integer, ForeignKey("carpetas.id"), nullable=False, index=True)
    usuario_subio_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    tipo_documento = Column(String(50), nullable=True)  # 'comprobante_pago', 'contrato', 'recibo', etc.
    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    carpeta = relationship("Carpeta", back_populates="documentos")
    usuario_subio = relationship("Usuario", back_populates="documentos_subidos")
