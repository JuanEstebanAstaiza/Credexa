from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Carpeta(Base):
    __tablename__ = "carpetas"
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)  # Multi-tenant
    nombre = Column(String(255), nullable=False, index=True)
    ruta_completa = Column(String(1000), nullable=False, index=True)  # Ruta completa desde raíz
    tipo = Column(String(50), nullable=False)  # 'mes', 'socio', 'cliente', 'prestamo', 'manual'
    parent_id = Column(Integer, ForeignKey("carpetas.id"), nullable=True, index=True)
    entidad_id = Column(Integer, nullable=True, index=True)  # ID del cliente o socio
    entidad_tipo = Column(String(20), nullable=True)  # 'cliente' o 'socio'
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=True, index=True)
    pago_id = Column(Integer, nullable=True, index=True)  # ID del pago relacionado
    es_automatica = Column(Boolean, default=False, nullable=False)
    descripcion = Column(Text, nullable=True)
    creada_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    empresa = relationship("Empresa", back_populates="carpetas")  # Multi-tenant
    parent = relationship("Carpeta", remote_side=[id], backref="subcarpetas")
    prestamo = relationship("Prestamo", back_populates="carpeta")
    usuario_creador = relationship("Usuario", back_populates="carpetas_creadas")
    documentos = relationship("Documento", back_populates="carpeta", cascade="all, delete-orphan")
