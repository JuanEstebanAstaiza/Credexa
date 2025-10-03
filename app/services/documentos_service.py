"""
Servicio para automatización de gestión de documentos
"""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.carpeta import Carpeta
from app.models.cliente import Cliente
from app.models.socio import Socio

# Directorio base para documentos
DOCUMENTOS_DIR = Path("documentos")
DOCUMENTOS_DIR.mkdir(exist_ok=True)

class DocumentosService:
    """Servicio para gestión automática de documentos y carpetas"""

    @staticmethod
    def crear_carpetas_mes_actual(db: Session) -> dict:
        """
        Crear estructura de carpetas para el mes actual.
        Se ejecuta automáticamente al inicio de cada mes.
        """
        ahora = datetime.now()
        mes_actual = ahora.strftime("%Y_%m")
        nombre_mes = ahora.strftime("%B_%Y").upper()  # EJEMPLO: OCTOBER_2024

        resultados = {
            "carpetas_creadas": [],
            "errores": []
        }

        try:
            # Verificar si ya existe la carpeta del mes
            carpeta_mes_existente = db.query(Carpeta).filter(
                and_(
                    Carpeta.tipo == "mes",
                    Carpeta.nombre == nombre_mes
                )
            ).first()

            if carpeta_mes_existente:
                resultados["errores"].append(f"Carpeta del mes {nombre_mes} ya existe")
                return resultados

            # Crear carpeta del mes
            carpeta_mes = Carpeta(
                nombre=nombre_mes,
                ruta_completa=nombre_mes,
                tipo="mes",
                es_automatica=True,
                descripcion=f"Carpeta automática para el mes {ahora.strftime('%B %Y')}"
            )

            db.add(carpeta_mes)
            db.flush()  # Para obtener el ID

            # Crear directorio físico
            dir_mes = DOCUMENTOS_DIR / nombre_mes
            dir_mes.mkdir(parents=True, exist_ok=True)

            resultados["carpetas_creadas"].append(f"Mes: {nombre_mes}")

            # Crear subcarpetas para socios activos
            socios_activos = db.query(Socio).filter(Socio.activo == 1).all()
            for socio in socios_activos:
                carpeta_socio = DocumentosService._crear_carpeta_socio(
                    db, socio, carpeta_mes.id, nombre_mes
                )
                if carpeta_socio:
                    resultados["carpetas_creadas"].append(f"Socio: {socio.nombre_completo}")
                else:
                    resultados["errores"].append(f"Error creando carpeta para socio {socio.nombre_completo}")

            # Crear subcarpetas para clientes activos
            clientes_activos = db.query(Cliente).filter(Cliente.activo == 1).all()
            for cliente in clientes_activos:
                carpeta_cliente = DocumentosService._crear_carpeta_cliente(
                    db, cliente, carpeta_mes.id, nombre_mes
                )
                if carpeta_cliente:
                    resultados["carpetas_creadas"].append(f"Cliente: {cliente.nombre_completo}")
                else:
                    resultados["errores"].append(f"Error creando carpeta para cliente {cliente.nombre_completo}")

            db.commit()
            resultados["exito"] = True

        except Exception as e:
            db.rollback()
            resultados["errores"].append(f"Error general: {str(e)}")
            resultados["exito"] = False

        return resultados

    @staticmethod
    def crear_carpeta_pago(db: Session, pago_id: int, tipo_entidad: str, entidad_id: int, prestamo_id: Optional[int] = None) -> Optional[Carpeta]:
        """
        Crear carpeta automática para un pago específico.
        Se llama cuando se registra un pago.
        """
        try:
            ahora = datetime.now()
            nombre_mes = ahora.strftime("%B_%Y").upper()

            # Obtener carpeta del mes actual
            carpeta_mes = db.query(Carpeta).filter(
                and_(
                    Carpeta.tipo == "mes",
                    Carpeta.nombre == nombre_mes
                )
            ).first()

            if not carpeta_mes:
                # Si no existe carpeta del mes, crearla
                resultado_mes = DocumentosService.crear_carpetas_mes_actual(db)
                if not resultado_mes.get("exito", False):
                    return None

                carpeta_mes = db.query(Carpeta).filter(
                    and_(
                        Carpeta.tipo == "mes",
                        Carpeta.nombre == nombre_mes
                    )
                ).first()

                if not carpeta_mes:
                    return None

            # Buscar carpeta de la entidad (cliente o socio)
            carpeta_entidad = db.query(Carpeta).filter(
                and_(
                    Carpeta.parent_id == carpeta_mes.id,
                    Carpeta.tipo == tipo_entidad,
                    Carpeta.entidad_id == entidad_id
                )
            ).first()

            if not carpeta_entidad:
                # Si no existe, crearla según el tipo
                if tipo_entidad == "cliente":
                    cliente = db.query(Cliente).filter(Cliente.id == entidad_id).first()
                    if cliente:
                        carpeta_entidad = DocumentosService._crear_carpeta_cliente(
                            db, cliente, carpeta_mes.id, carpeta_mes.ruta_completa
                        )
                elif tipo_entidad == "socio":
                    socio = db.query(Socio).filter(Socio.id == entidad_id).first()
                    if socio:
                        carpeta_entidad = DocumentosService._crear_carpeta_socio(
                            db, socio, carpeta_mes.id, carpeta_mes.ruta_completa
                        )

                if not carpeta_entidad:
                    return None

            # Crear subcarpeta de Pagos si no existe
            carpeta_pagos = db.query(Carpeta).filter(
                and_(
                    Carpeta.parent_id == carpeta_entidad.id,
                    Carpeta.nombre == "Pagos",
                    Carpeta.tipo == "pagos"
                )
            ).first()

            if not carpeta_pagos:
                carpeta_pagos = Carpeta(
                    nombre="Pagos",
                    ruta_completa=f"{carpeta_entidad.ruta_completa}/Pagos",
                    tipo="pagos",
                    parent_id=carpeta_entidad.id,
                    entidad_id=entidad_id,
                    entidad_tipo=tipo_entidad,
                    es_automatica=True,
                    descripcion=f"Carpeta automática para pagos de {tipo_entidad}"
                )

                db.add(carpeta_pagos)
                db.flush()

                # Crear directorio físico
                dir_pagos = DOCUMENTOS_DIR / carpeta_pagos.ruta_completa
                dir_pagos.mkdir(parents=True, exist_ok=True)

            # Crear carpeta específica para el pago
            nombre_pago = f"Pago_{pago_id}"
            if prestamo_id:
                nombre_pago += f"_Prestamo_{prestamo_id}"

            ruta_pago = f"{carpeta_pagos.ruta_completa}/{nombre_pago}"

            carpeta_pago = Carpeta(
                nombre=nombre_pago,
                ruta_completa=ruta_pago,
                tipo="pago",
                parent_id=carpeta_pagos.id,
                entidad_id=entidad_id,
                entidad_tipo=tipo_entidad,
                prestamo_id=prestamo_id,
                pago_id=pago_id,
                es_automatica=True,
                descripcion=f"Carpeta automática para pago #{pago_id}"
            )

            db.add(carpeta_pago)
            db.flush()

            # Crear directorio físico
            dir_pago = DOCUMENTOS_DIR / ruta_pago
            dir_pago.mkdir(parents=True, exist_ok=True)

            db.commit()
            return carpeta_pago

        except Exception as e:
            db.rollback()
            print(f"Error creando carpeta de pago: {e}")
            return None

    @staticmethod
    def subir_documento_automatico(db: Session, archivo, carpeta_id: int, tipo_documento: str = "comprobante_pago",
                                  descripcion: str = "", usuario_id: int = None) -> Optional[dict]:
        """
        Subir un documento automáticamente a una carpeta específica.
        """
        from app.models.documento import Documento
        import uuid

        try:
            # Obtener la carpeta
            carpeta = db.query(Carpeta).filter(Carpeta.id == carpeta_id).first()
            if not carpeta:
                return None

            # Generar nombre único para el archivo
            extension = Path(archivo.filename).suffix.lower()
            nombre_unico = f"{uuid.uuid4()}{extension}"
            ruta_archivo = f"{carpeta.ruta_completa}/{nombre_unico}"

            # Guardar archivo físicamente
            ruta_completa = DOCUMENTOS_DIR / ruta_archivo
            ruta_completa.parent.mkdir(parents=True, exist_ok=True)

            with open(ruta_completa, "wb") as f:
                f.write(archivo.file.read())

            # Crear registro en base de datos
            documento = Documento(
                nombre_original=archivo.filename,
                nombre_archivo=nombre_unico,
                ruta_archivo=ruta_archivo,
                tipo_mime=archivo.content_type,
                tamano=ruta_completa.stat().st_size,
                descripcion=descripcion,
                tipo_documento=tipo_documento,
                carpeta_id=carpeta_id,
                usuario_subio_id=usuario_id
            )

            db.add(documento)
            db.commit()

            return {
                "id": documento.id,
                "nombre_original": documento.nombre_original,
                "ruta_archivo": documento.ruta_archivo,
                "tipo_documento": documento.tipo_documento
            }

        except Exception as e:
            db.rollback()
            print(f"Error subiendo documento automático: {e}")
            return None

    @staticmethod
    def crear_carpeta_prestamo(db: Session, prestamo_id: int, cliente_id: int) -> Optional[Carpeta]:
        """
        Crear carpeta automática para un préstamo específico.
        Se llama cuando se crea un nuevo préstamo.
        """
        try:
            # Obtener el cliente
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return None

            # Obtener la carpeta del mes actual para este cliente
            ahora = datetime.now()
            nombre_mes = ahora.strftime("%B_%Y").upper()

            carpeta_mes = db.query(Carpeta).filter(
                and_(
                    Carpeta.tipo == "mes",
                    Carpeta.nombre == nombre_mes
                )
            ).first()

            if not carpeta_mes:
                # Si no existe carpeta del mes, crearla primero
                resultado_mes = DocumentosService.crear_carpetas_mes_actual(db)
                if not resultado_mes.get("exito", False):
                    return None

                carpeta_mes = db.query(Carpeta).filter(
                    and_(
                        Carpeta.tipo == "mes",
                        Carpeta.nombre == nombre_mes
                    )
                ).first()

                if not carpeta_mes:
                    return None

            # Buscar carpeta del cliente dentro del mes
            carpeta_cliente = db.query(Carpeta).filter(
                and_(
                    Carpeta.parent_id == carpeta_mes.id,
                    Carpeta.tipo == "cliente",
                    Carpeta.entidad_id == cliente_id
                )
            ).first()

            if not carpeta_cliente:
                # Si no existe, crearla
                carpeta_cliente = DocumentosService._crear_carpeta_cliente(
                    db, cliente, carpeta_mes.id, carpeta_mes.ruta_completa
                )
                if not carpeta_cliente:
                    return None

            # Crear carpeta específica para el préstamo
            nombre_prestamo = f"Prestamo_{prestamo_id}"
            ruta_prestamo = f"{carpeta_cliente.ruta_completa}/{nombre_prestamo}"

            carpeta_prestamo = Carpeta(
                nombre=nombre_prestamo,
                ruta_completa=ruta_prestamo,
                tipo="prestamo",
                parent_id=carpeta_cliente.id,
                entidad_id=cliente_id,
                entidad_tipo="cliente",
                prestamo_id=prestamo_id,
                es_automatica=True,
                descripcion=f"Carpeta automática para préstamo #{prestamo_id}"
            )

            db.add(carpeta_prestamo)
            db.flush()

            # Crear directorio físico
            dir_prestamo = DOCUMENTOS_DIR / ruta_prestamo
            dir_prestamo.mkdir(parents=True, exist_ok=True)

            db.commit()
            return carpeta_prestamo

        except Exception as e:
            db.rollback()
            print(f"Error creando carpeta de préstamo: {e}")
            return None

    @staticmethod
    def _crear_carpeta_socio(db: Session, socio: Socio, parent_id: int, ruta_padre: str) -> Optional[Carpeta]:
        """Crear carpeta para un socio específico"""
        try:
            nombre_socio = f"Socio_{socio.id}_{socio.nombre_completo.replace(' ', '_')}"
            ruta_completa = f"{ruta_padre}/{nombre_socio}"

            carpeta_socio = Carpeta(
                nombre=nombre_socio,
                ruta_completa=ruta_completa,
                tipo="socio",
                parent_id=parent_id,
                entidad_id=socio.id,
                entidad_tipo="socio",
                es_automatica=True,
                descripcion=f"Carpeta automática para socio {socio.nombre_completo}"
            )

            db.add(carpeta_socio)

            # Crear directorio físico
            dir_socio = DOCUMENTOS_DIR / ruta_completa
            dir_socio.mkdir(parents=True, exist_ok=True)

            return carpeta_socio

        except Exception as e:
            print(f"Error creando carpeta para socio {socio.nombre_completo}: {e}")
            return None

    @staticmethod
    def _crear_carpeta_cliente(db: Session, cliente: Cliente, parent_id: int, ruta_padre: str) -> Optional[Carpeta]:
        """Crear carpeta para un cliente específico"""
        try:
            nombre_cliente = f"Cliente_{cliente.id}_{cliente.nombre_completo.replace(' ', '_')}"
            ruta_completa = f"{ruta_padre}/{nombre_cliente}"

            carpeta_cliente = Carpeta(
                nombre=nombre_cliente,
                ruta_completa=ruta_completa,
                tipo="cliente",
                parent_id=parent_id,
                entidad_id=cliente.id,
                entidad_tipo="cliente",
                es_automatica=True,
                descripcion=f"Carpeta automática para cliente {cliente.nombre_completo}"
            )

            db.add(carpeta_cliente)

            # Crear directorio físico
            dir_cliente = DOCUMENTOS_DIR / ruta_completa
            dir_cliente.mkdir(parents=True, exist_ok=True)

            return carpeta_cliente

        except Exception as e:
            print(f"Error creando carpeta para cliente {cliente.nombre_completo}: {e}")
            return None

    @staticmethod
    def verificar_estructura_carpetas(db: Session) -> dict:
        """
        Verificar la integridad de la estructura de carpetas
        y crear las que faltan si es necesario
        """
        resultados = {
            "carpetas_verificadas": 0,
            "directorios_creados": 0,
            "errores": []
        }

        try:
            # Verificar todas las carpetas en BD
            carpetas = db.query(Carpeta).all()

            for carpeta in carpetas:
                dir_path = DOCUMENTOS_DIR / carpeta.ruta_completa

                if not dir_path.exists():
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        resultados["directorios_creados"] += 1
                    except Exception as e:
                        resultados["errores"].append(
                            f"Error creando directorio {carpeta.ruta_completa}: {e}"
                        )

                resultados["carpetas_verificadas"] += 1

            resultados["exito"] = True

        except Exception as e:
            resultados["errores"].append(f"Error general en verificación: {e}")
            resultados["exito"] = False

        return resultados

    @staticmethod
    def limpiar_carpetas_vacias(db: Session) -> dict:
        """
        Limpiar carpetas vacías que no sean automáticas
        """
        resultados = {
            "carpetas_eliminadas": [],
            "errores": []
        }

        try:
            # Buscar carpetas manuales sin contenido
            carpetas_vacias = db.query(Carpeta).filter(
                and_(
                    Carpeta.es_automatica == False,
                    ~Carpeta.subcarpetas.any(),  # Sin subcarpetas
                    ~Carpeta.documentos.any()   # Sin documentos
                )
            ).all()

            for carpeta in carpetas_vacias:
                try:
                    # Eliminar directorio físico si existe
                    dir_path = DOCUMENTOS_DIR / carpeta.ruta_completa
                    if dir_path.exists():
                        dir_path.rmdir()  # Solo elimina si está vacío

                    # Eliminar de BD
                    db.delete(carpeta)
                    resultados["carpetas_eliminadas"].append(carpeta.nombre)

                except Exception as e:
                    resultados["errores"].append(
                        f"Error eliminando carpeta {carpeta.nombre}: {e}"
                    )

            db.commit()
            resultados["exito"] = True

        except Exception as e:
            db.rollback()
            resultados["errores"].append(f"Error general: {e}")
            resultados["exito"] = False

        return resultados
