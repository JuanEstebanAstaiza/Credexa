"""
Servicio de envío de correos electrónicos
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para envío de correos electrónicos"""

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.use_ssl = settings.SMTP_USE_SSL
        self.email_from = settings.EMAIL_FROM
        self.email_from_name = settings.EMAIL_FROM_NAME

    def is_configured(self) -> bool:
        """Verifica si el servicio de email está configurado"""
        return bool(
            self.smtp_server and
            self.smtp_username and
            self.smtp_password and
            self.email_from
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc_emails: Optional[list] = None
    ) -> bool:
        """
        Envía un correo electrónico

        Args:
            to_email: Email del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional)
            cc_emails: Lista de emails en copia (opcional)

        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        if not self.is_configured():
            logger.warning("Servicio de email no configurado")
            return False

        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = f"{self.email_from_name} <{self.email_from}>"
            msg['To'] = to_email

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # Agregar contenido de texto plano
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)

            # Agregar contenido HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Conectar al servidor SMTP
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.use_tls and not self.use_ssl:
                server.starttls()

            # Autenticar
            server.login(self.smtp_username, self.smtp_password)

            # Enviar email
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)

            server.sendmail(self.email_from, recipients, msg.as_string())
            server.quit()

            logger.info(f"Email enviado exitosamente a {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {str(e)}")
            return False

    def send_password_change_notification(
        self,
        user_email: str,
        user_name: str,
        new_password: str,
        changed_by_admin: bool = False,
        admin_name: Optional[str] = None
    ) -> bool:
        """
        Envía notificación de cambio de contraseña

        Args:
            user_email: Email del usuario
            user_name: Nombre del usuario
            new_password: Nueva contraseña
            changed_by_admin: Si fue cambiada por un administrador
            admin_name: Nombre del administrador que realizó el cambio
        """
        if changed_by_admin and admin_name:
            subject = f"🔐 Contraseña actualizada - {settings.APP_NAME}"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Contraseña Actualizada</title>
            </head>
            <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                        <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 36px;">🔐</span>
                        </div>
                        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Contraseña Actualizada</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">{settings.APP_NAME}</p>
                    </div>

                    <!-- Content -->
                    <div style="padding: 40px 30px;">
                        <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">Hola {user_name},</h2>

                        <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px;">
                            Tu contraseña ha sido actualizada por el administrador <strong style="color: #667eea;">{admin_name}</strong>.
                        </p>

                        <!-- Password Box -->
                        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center; box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);">
                            <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 28px;">🔑</span>
                            </div>
                            <h3 style="color: white; margin: 0 0 15px; font-size: 20px;">Tu Nueva Contraseña</h3>
                            <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 8px; padding: 15px; display: inline-block;">
                                <code style="font-size: 24px; font-weight: bold; color: white; font-family: 'Courier New', monospace; letter-spacing: 2px;">
                                    {new_password}
                                </code>
                            </div>
                        </div>

                        <!-- Warning Alert -->
                        <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); border-left: 4px solid #ff6b35; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <div style="display: flex; align-items: flex-start;">
                                <span style="font-size: 24px; margin-right: 15px;">⚠️</span>
                                <div>
                                    <h4 style="color: #d2691e; margin: 0 0 10px; font-size: 18px;">Importante</h4>
                                    <p style="color: #8b4513; margin: 0; font-size: 14px;">
                                        Te recomendamos cambiar esta contraseña temporal lo antes posible por una de tu preferencia desde tu perfil de usuario.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Security Note -->
                        <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); border-left: 4px solid #e17055; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <div style="display: flex; align-items: flex-start;">
                                <span style="font-size: 24px; margin-right: 15px;">🛡️</span>
                                <div>
                                    <h4 style="color: #d63031; margin: 0 0 10px; font-size: 18px;">¿No solicitaste este cambio?</h4>
                                    <p style="color: #636e72; margin: 0; font-size: 14px;">
                                        Si no solicitaste este cambio de contraseña, contacta inmediatamente al administrador para reportar esta actividad.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px; text-align: center;">
                            <p style="color: #999; font-size: 14px; margin: 0;">
                                <strong>{settings.APP_NAME}</strong><br>
                                Sistema de Gestión de Préstamos<br>
                                <span style="color: #ccc;">Este es un mensaje automático. Por favor, no respondas a este correo.</span>
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = f"✅ Contraseña cambiada exitosamente - {settings.APP_NAME}"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Contraseña Cambiada</title>
            </head>
            <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); padding: 40px 30px; text-align: center;">
                        <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 36px;">✅</span>
                        </div>
                        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Contraseña Cambiada</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">{settings.APP_NAME}</p>
                    </div>

                    <!-- Content -->
                    <div style="padding: 40px 30px;">
                        <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">¡Hola {user_name}!</h2>

                        <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px;">
                            Tu contraseña ha sido cambiada exitosamente. Ya puedes acceder al sistema con tu nueva contraseña.
                        </p>

                        <!-- Password Box -->
                        <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center; box-shadow: 0 8px 20px rgba(9, 132, 227, 0.15);">
                            <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 28px;">🔑</span>
                            </div>
                            <h3 style="color: white; margin: 0 0 15px; font-size: 20px;">Tu Nueva Contraseña</h3>
                            <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 8px; padding: 15px; display: inline-block;">
                                <code style="font-size: 24px; font-weight: bold; color: white; font-family: 'Courier New', monospace; letter-spacing: 2px;">
                                    {new_password}
                                </code>
                            </div>
                        </div>

                        <!-- Success Alert -->
                        <div style="background: linear-gradient(135deg, #55efc4 0%, #00b894 100%); border-left: 4px solid #00b894; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <div style="display: flex; align-items: flex-start;">
                                <span style="font-size: 24px; margin-right: 15px;">🎉</span>
                                <div>
                                    <h4 style="color: #00684a; margin: 0 0 10px; font-size: 18px;">¡Cambio exitoso!</h4>
                                    <p style="color: #004d36; margin: 0; font-size: 14px;">
                                        Tu contraseña se ha actualizado correctamente. Ya puedes iniciar sesión con las nuevas credenciales.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Security Tip -->
                        <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); border-left: 4px solid #e17055; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <div style="display: flex; align-items: flex-start;">
                                <span style="font-size: 24px; margin-right: 15px;">💡</span>
                                <div>
                                    <h4 style="color: #d63031; margin: 0 0 10px; font-size: 18px;">Recomendación de Seguridad</h4>
                                    <p style="color: #636e72; margin: 0; font-size: 14px;">
                                        Te recomendamos cambiar esta contraseña por una más personalizada y segura desde tu perfil de usuario.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px; text-align: center;">
                            <p style="color: #999; font-size: 14px; margin: 0;">
                                <strong>{settings.APP_NAME}</strong><br>
                                Sistema de Gestión de Préstamos<br>
                                <span style="color: #ccc;">Este es un mensaje automático. Por favor, no respondas a este correo.</span>
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

        return self.send_email(user_email, subject, html_content)

    def send_password_request_confirmation(
        self,
        user_email: str,
        user_name: str
    ) -> bool:
        """
        Envía confirmación de solicitud de cambio de contraseña

        Args:
            user_email: Email del usuario
            user_name: Nombre del usuario
        """
        subject = f"📋 Solicitud de cambio de contraseña recibida - {settings.APP_NAME}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Solicitud Recibida</title>
        </head>
        <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 40px 30px; text-align: center;">
                    <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 36px;">📋</span>
                    </div>
                    <h1 style="color: #333; margin: 0; font-size: 28px; font-weight: 600;">Solicitud Recibida</h1>
                    <p style="color: #666; margin: 10px 0 0; font-size: 16px;">{settings.APP_NAME}</p>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">Hola {user_name},</h2>

                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px;">
                        Hemos recibido exitosamente tu solicitud de cambio de contraseña.
                    </p>

                    <!-- Status Box -->
                    <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center; box-shadow: 0 8px 20px rgba(231, 112, 85, 0.15);">
                        <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 28px;">⏳</span>
                        </div>
                        <h3 style="color: #d63031; margin: 0 0 15px; font-size: 20px;">Estado: Pendiente de Revisión</h3>
                        <p style="color: #636e72; margin: 0; font-size: 14px;">
                            Un administrador revisará tu solicitud y procesará el cambio de contraseña en breve.
                        </p>
                    </div>

                    <!-- Info Alert -->
                    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-left: 4px solid #0984e3; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 24px; margin-right: 15px;">📧</span>
                            <div>
                                <h4 style="color: white; margin: 0 0 10px; font-size: 18px;">Notificación Automática</h4>
                                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                                    Te enviaremos un email cuando tu solicitud sea procesada por el administrador.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Contact Info -->
                    <div style="background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%); border-left: 4px solid #e84393; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 24px; margin-right: 15px;">🚨</span>
                            <div>
                                <h4 style="color: #c44569; margin: 0 0 10px; font-size: 18px;">¿Tienes Urgencia?</h4>
                                <p style="color: #6c5ce7; margin: 0; font-size: 14px;">
                                    Si necesitas cambiar tu contraseña urgentemente, contacta directamente al administrador.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px; text-align: center;">
                        <p style="color: #999; font-size: 14px; margin: 0;">
                            <strong>{settings.APP_NAME}</strong><br>
                            Sistema de Gestión de Préstamos<br>
                            <span style="color: #ccc;">Este es un mensaje automático. Por favor, no respondas a este correo.</span>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    def send_password_request_processed(
        self,
        user_email: str,
        user_name: str,
        approved: bool,
        admin_name: str,
        new_password: Optional[str] = None,
        comments: Optional[str] = None
    ) -> bool:
        """
        Envía notificación cuando una solicitud de contraseña es procesada

        Args:
            user_email: Email del usuario
            user_name: Nombre del usuario
            approved: Si fue aprobada o rechazada
            admin_name: Nombre del administrador
            new_password: Nueva contraseña (solo si fue aprobada)
            comments: Comentarios del administrador
        """
        if approved:
            subject = f"✅ Solicitud de contraseña aprobada - {settings.APP_NAME}"
            status_color = "#00b894"
            status_bg = "linear-gradient(135deg, #00b894 0%, #00cec9 100%)"
            status_icon = "✅"
            status_text = "APROBADA"
        else:
            subject = f"❌ Solicitud de contraseña rechazada - {settings.APP_NAME}"
            status_color = "#e84393"
            status_bg = "linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%)"
            status_icon = "❌"
            status_text = "RECHAZADA"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Solicitud Procesada</title>
        </head>
        <body style="margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background: {status_bg}; padding: 40px 30px; text-align: center;">
                    <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 36px;">{status_icon}</span>
                    </div>
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Solicitud Procesada</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">{settings.APP_NAME}</p>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">Hola {user_name},</h2>

                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px;">
                        Tu solicitud de cambio de contraseña ha sido procesada por el administrador.
                    </p>

                    <!-- Status Box -->
                    <div style="background: {status_bg}; border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center; box-shadow: 0 8px 20px rgba(0, 184, 148, 0.15);">
                        <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 28px;">{status_icon}</span>
                        </div>
                        <h3 style="color: white; margin: 0 0 15px; font-size: 22px;">Estado: {status_text}</h3>
                        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                            Procesada por: <strong>{admin_name}</strong>
                        </p>
                    </div>
        """

        if approved and new_password:
            html_content += f"""
                    <!-- Password Box -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center; box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);">
                        <div style="width: 60px; height: 60px; background: rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 28px;">🔑</span>
                        </div>
                        <h3 style="color: white; margin: 0 0 15px; font-size: 20px;">Tu Nueva Contraseña</h3>
                        <div style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 8px; padding: 15px; display: inline-block;">
                            <code style="font-size: 24px; font-weight: bold; color: white; font-family: 'Courier New', monospace; letter-spacing: 2px;">
                                {new_password}
                            </code>
                        </div>
                        <p style="color: rgba(255,255,255,0.9); margin: 15px 0 0; font-size: 14px;">
                            <em>Guarda esta contraseña y cambia a una más personalizada cuando inicies sesión.</em>
                        </p>
                    </div>
            """

        if comments:
            html_content += f"""
                    <!-- Comments Box -->
                    <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); border-left: 4px solid #e17055; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 24px; margin-right: 15px;">💬</span>
                            <div>
                                <h4 style="color: #d63031; margin: 0 0 10px; font-size: 18px;">Comentarios del Administrador</h4>
                                <blockquote style="background: rgba(255,255,255,0.7); border-left: 3px solid #e17055; padding: 15px; margin: 0; border-radius: 6px; font-style: italic; color: #636e72;">
                                    "{comments}"
                                </blockquote>
                            </div>
                        </div>
                    </div>
            """

        html_content += f"""
                    <!-- Contact Info -->
                    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-left: 4px solid #0984e3; padding: 20px; border-radius: 8px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 24px; margin-right: 15px;">📞</span>
                            <div>
                                <h4 style="color: white; margin: 0 0 10px; font-size: 18px;">¿Tienes Preguntas?</h4>
                                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                                    Si tienes alguna pregunta sobre tu solicitud, contacta al administrador.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div style="border-top: 1px solid #eee; padding-top: 30px; margin-top: 30px; text-align: center;">
                        <p style="color: #999; font-size: 14px; margin: 0;">
                            <strong>{settings.APP_NAME}</strong><br>
                            Sistema de Gestión de Préstamos<br>
                            <span style="color: #ccc;">Este es un mensaje automático. Por favor, no respondas a este correo.</span>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)


# Instancia global del servicio
email_service = EmailService()
