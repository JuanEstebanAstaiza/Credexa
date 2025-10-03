# Configuración de Email SMTP

Este documento explica cómo configurar el servicio de envío de correos electrónicos para el sistema Credexa.

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# Email SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu.email@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicación
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Email de envío
EMAIL_FROM=tu.email@gmail.com
EMAIL_FROM_NAME=Credexa Sistema
```

## Configuraciones por Proveedor

### Gmail
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

**Importante:** Gmail requiere una "contraseña de aplicación", no tu contraseña normal.
1. Ve a [Google Account Settings](https://myaccount.google.com/security)
2. Activa la verificación en 2 pasos
3. Crea una "contraseña de aplicación" en "Contraseñas de aplicaciones"

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

**Importante:** Outlook también requiere "contraseña de aplicación".
1. Ve a [Microsoft Account Settings](https://account.microsoft.com/security/app-passwords)
2. Crea una contraseña de aplicación

### Office 365
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

## Configuración en la Interfaz

1. Inicia sesión como administrador
2. Ve a **Configuración** > **Configuración de Email**
3. Completa el formulario con tus credenciales SMTP
4. Haz clic en **"Guardar y Probar Configuración"**
5. Si funciona, recibirás un email de prueba

## Emails que se Envían

### Para Administradores
- ✅ Confirmación al cambiar su propia contraseña
- ✅ Notificación al cambiar contraseña de otros usuarios
- ✅ Procesamiento de solicitudes de usuarios

### Para Digitadores
- ✅ Confirmación de solicitud de cambio de contraseña
- ✅ Notificación cuando se procesa la solicitud (aprobada/rechazada)
- ✅ Nueva contraseña asignada

## Solución de Problemas

### Error de Autenticación
- Verifica que el usuario y contraseña SMTP sean correctos
- Para Gmail/Outlook, usa contraseñas de aplicación, no la contraseña normal

### Error de Conexión
- Verifica que el puerto sea correcto (587 para TLS, 465 para SSL)
- Asegúrate de que tu firewall permita conexiones SMTP

### Emails no llegan
- Revisa la carpeta de spam
- Verifica que la dirección del remitente esté autorizada
- Prueba enviando un email de prueba desde la interfaz

## Seguridad

- Las contraseñas SMTP se almacenan de forma segura (no en texto plano)
- Se recomienda usar contraseñas de aplicación en lugar de contraseñas principales
- Los emails contienen información sensible, así que configura correctamente el SMTP

## Configuración por Defecto

Si no configuras el email, el sistema seguirá funcionando normalmente, pero no enviará notificaciones por email.
