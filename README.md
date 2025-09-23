# Credexa - Sistema de Gestión Financiera

Aplicación web completa para la gestión financiera de pequeñas empresas, desarrollada con FastAPI y SQLite. Sistema profesional con todas las funcionalidades necesarias para administrar créditos, clientes, pagos y reportes.

## ✨ Características Principales

### 🔐 Módulo de Autenticación y Usuarios ✅ COMPLETO
- ✅ Login seguro con JWT tokens y cookies
- ✅ Sistema de roles (Administrador / Digitador)
- ✅ Gestión completa de usuarios (crear, editar, activar/desactivar, reset de contraseña)
- ✅ **Perfil de usuario editable** con cambio de contraseña
- ✅ Interfaz web moderna con Bootstrap 5 y HTMX

### 👥 Módulo de Clientes ✅ COMPLETO
- ✅ Registro completo de clientes (datos personales, contacto, financieros)
- ✅ Validaciones avanzadas (cédula, email, teléfono)
- ✅ Listado con búsqueda y filtros avanzados
- ✅ Edición/actualización de datos
- ✅ Historial completo por cliente

### 💰 Módulo de Créditos ✅ COMPLETO
- ✅ Creación de créditos con cálculo automático de amortización
- ✅ Sistema de cuotas con intereses y capital
- ✅ Estados: Activo, Pagado, Vencido
- ✅ Cálculo financiero completo (tasa de interés, plazo, valor cuota)
- ✅ Detalles completos con progreso de pago

### 💳 Módulo de Pagos ✅ COMPLETO
- ✅ Registro manual de pagos (cuotas completas o parciales)
- ✅ Cálculo automático de capital vs intereses
- ✅ Actualización automática de saldos y estados
- ✅ Historial completo por cliente y crédito
- ✅ Validaciones de pagos y montos

### 📊 Módulo de Reportes ✅ COMPLETO
- ✅ Dashboard con estadísticas en tiempo real
- ✅ **Gráficos interactivos** con Chart.js
- ✅ Reportes de pagos por fechas y filtros
- ✅ Reportes de clientes morosos
- ✅ **Exportación múltiple**: Excel, PDF, CSV
- ✅ **Impresión profesional** con formato estilizado
- ✅ Filtros avanzados por fechas, montos, tipos

### ⚙️ Módulo de Configuración ✅ COMPLETO
- ✅ Gestión de configuraciones del sistema (19 parámetros)
- ✅ Configuraciones por defecto incluidas
- ✅ Interfaz completa para gestión de usuarios
- ✅ Parámetros financieros (tasas, límites, días de gracia)
- ✅ Control de acceso administrativo completo

### 🎛️ Panel de Control (Dashboard) ✅ COMPLETO
- ✅ Vista general con métricas clave
- ✅ Estadísticas en tiempo real
- ✅ Gráficas de distribución y evolución
- ✅ Alertas y notificaciones
- ✅ Navegación intuitiva

## 🛠️ Tecnologías Utilizadas

- **Backend**: FastAPI (framework moderno de Python)
- **Base de Datos**: SQLite (embebida, sin configuración)
- **ORM**: SQLAlchemy con SQLAlchemy ORM
- **Autenticación**: JWT Tokens + bcrypt para hashing
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **UI Framework**: Bootstrap 5
- **Interactividad**: HTMX (sin JavaScript complejo)
- **Gráficos**: Chart.js (librería profesional)
- **Reportes**: ReportLab (PDF), pandas/openpyxl (Excel), CSV nativo
- **Iconos**: Font Awesome 6
- **Templates**: Jinja2

## 🚀 Instalación y Configuración

### Requisitos Previos

- **Python 3.8 o superior**
- **pip** (gestor de paquetes de Python)
- **Navegador web moderno** (Chrome, Firefox, Edge)

### Instalación Rápida

1. **Clonar o descargar el proyecto**
   ```bash
   cd GestionPrestamos
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```
   > **Nota**: Las dependencias incluyen pandas, reportlab, openpyxl para reportes avanzados

3. **Inicializar la base de datos**
   ```bash
   python init_db.py
   ```
   > **Nota**: Esto crea usuarios iniciales, configuraciones por defecto y datos de ejemplo

4. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

5. **Acceder a Credexa**
   - 🌐 **URL**: `http://127.0.0.1:8000`
   - 👤 **Usuario**: `admin`
   - 🔑 **Contraseña**: `admin123`

## 👥 Usuarios Iniciales

Después de ejecutar `init_db.py`, se crean automáticamente:

### 👑 Administrador
- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Email**: `admin@credexa.com`
- **Rol**: Administrador
- **Permisos**: Acceso completo a todas las funcionalidades

### 👤 Digitador
- **Usuario**: `digitador`
- **Contraseña**: `digitador123`
- **Email**: `digitador@credexa.com`
- **Rol**: Digitador
- **Permisos**: Gestión de clientes, créditos y pagos

> **💡 Tip**: El administrador puede crear usuarios adicionales desde **Configuración > Gestión de Usuarios**

## 📁 Estructura del Proyecto

```
GestionPrestamos/
├── 📄 main.py                    # 🚀 Punto de entrada de la aplicación
├── 📄 init_db.py                 # 🗄️ Script de inicialización de BD
├── 📄 create_prestamos_table.py  # 💰 Script para crear datos de ejemplo
├── 📄 requirements.txt           # 📦 Dependencias del proyecto
├── 📄 README.md                  # 📖 Este archivo
├── 📁 app/                       # 📱 Código principal de la aplicación
│   ├── 📄 __init__.py
│   ├── 📁 api/                   # 🔌 APIs REST
│   │   ├── 📄 __init__.py
│   │   ├── 📄 api.py             # 🛣️ Router principal de la API
│   │   ├── 📄 auth.py            # 🔐 Endpoints de autenticación y perfil
│   │   ├── 📄 clientes.py        # 👥 Gestión de clientes
│   │   ├── 📄 prestamos.py       # 💰 Gestión de créditos
│   │   ├── 📄 pagos.py           # 💳 Gestión de pagos
│   │   ├── 📄 reportes.py        # 📊 APIs de reportes y exportaciones
│   │   └── 📄 configuracion.py   # ⚙️ Configuración del sistema
│   ├── 📁 core/                  # ⚙️ Configuración central
│   │   ├── 📄 __init__.py
│   │   ├── 📄 config.py          # 🔧 Configuración de la aplicación
│   │   ├── 📄 database.py        # 🗄️ Configuración de base de datos
│   │   └── 📄 security.py        # 🔒 Utilidades de seguridad y JWT
│   ├── 📁 models/                # 📋 Modelos de base de datos
│   │   ├── 📄 __init__.py
│   │   ├── 📄 user.py            # 👤 Modelos de Usuario y Rol
│   │   ├── 📄 cliente.py         # 👥 Modelo de Cliente
│   │   ├── 📄 prestamo.py        # 💰 Modelo de Crédito
│   │   ├── 📄 pago.py            # 💳 Modelo de Pago
│   │   └── 📄 configuracion.py   # ⚙️ Modelo de Configuración
│   ├── 📁 schemas/               # 📝 Esquemas Pydantic
│   │   ├── 📄 __init__.py
│   │   ├── 📄 user.py            # 👤 Esquemas de usuario
│   │   ├── 📄 cliente.py         # 👥 Esquemas de cliente
│   │   ├── 📄 prestamo.py        # 💰 Esquemas de crédito
│   │   ├── 📄 pago.py            # 💳 Esquemas de pago
│   │   ├── 📄 reporte.py         # 📊 Esquemas de reportes
│   │   └── 📄 configuracion.py   # ⚙️ Esquemas de configuración
│   ├── 📁 static/                # 🎨 Archivos estáticos
│   │   ├── 📁 css/
│   │   │   └── 📄 style.css      # 🎨 Estilos personalizados
│   │   └── 📁 js/
│   │       ├── 📄 app.js         # ⚡ JavaScript principal
│   │       └── 📄 chart.js       # 📊 Librería Chart.js
│   └── 📁 templates/             # 🎭 Templates HTML
│       ├── 📄 base.html          # 🏠 Template base
│       ├── 📄 dashboard.html     # 🏠 Dashboard principal
│       ├── 📄 perfil.html        # 👤 Página de perfil de usuario
│       ├── 📁 auth/              # 🔐 Autenticación
│       │   └── 📄 login.html     # 🚪 Página de login
│       ├── 📁 clientes/          # 👥 Clientes
│       │   ├── 📄 lista.html     # 📋 Listado de clientes
│       │   └── 📄 formulario.html # 📝 Formulario cliente
│       ├── 📁 prestamos/         # 💰 Créditos
│       │   ├── 📄 lista.html     # 📋 Listado de créditos
│       │   ├── 📄 formulario.html # 📝 Formulario de crédito
│       │   └── 📄 detalle.html   # 📄 Detalles del crédito
│       ├── 📁 pagos/             # 💳 Pagos
│       │   ├── 📄 lista.html     # 📋 Listado de pagos
│       │   ├── 📄 registrar.html # 💰 Registrar pago
│       │   └── 📄 detalle.html   # 📄 Detalles del pago
│       ├── 📁 reportes/          # 📊 Reportes
│       │   ├── 📄 index.html     # 🏠 Dashboard de reportes
│       │   ├── 📄 pagos.html     # 💰 Reporte de pagos
│       │   └── 📄 morosos.html   # ⚠️ Reporte de morosos
│       └── 📁 configuracion/     # ⚙️ Configuración
│           ├── 📄 index.html     # 🏠 Configuración principal
│           ├── 📄 usuarios.html  # 👥 Gestión de usuarios
│           └── 📄 sistema.html   # ⚙️ Parámetros del sistema
├── 📁 instance/                  # 💾 Base de datos y archivos
│   └── 📄 sql_app.db            # 🗄️ Base de datos SQLite
└── 📄 .env                      # 🔐 Variables de entorno (opcional)
```

## 🎯 Uso de Credexa

### Acceso Rápido
1. 🌐 Abrir `http://127.0.0.1:8000` en el navegador
2. 🔑 Iniciar sesión con credenciales de administrador o digitador
3. 📊 Acceder al dashboard principal

### 📍 URLs Principales
- **🏠 Dashboard**: `/` o `/dashboard`
- **👤 Mi Perfil**: `/perfil`
- **👥 Clientes**: `/clientes`
- **💰 Créditos**: `/prestamos`
- **💳 Pagos**: `/pagos`
- **📊 Reportes**: `/reportes`
- **⚙️ Configuración**: `/configuracion` (solo admin)

### 🔌 Documentación de API
- **📚 Swagger UI**: `http://127.0.0.1:8000/docs`
- **📖 ReDoc**: `http://127.0.0.1:8000/redoc`

## ✅ Funcionalidades Completas

### 🔐 Sistema de Autenticación
- ✅ Login seguro con JWT tokens
- ✅ Sesiones persistentes con cookies
- ✅ Sistema de roles (Administrador/Digitador)
- ✅ **Perfil de usuario editable**
- ✅ Cambio de contraseña seguro
- ✅ Gestión completa de usuarios (solo admin)

### 👥 Gestión de Clientes
- ✅ Registro completo con validaciones
- ✅ Datos personales, contacto y financieros
- ✅ Búsqueda y filtros avanzados
- ✅ Edición/actualización de información
- ✅ Historial completo por cliente

### 💰 Sistema de Créditos
- ✅ Creación con cálculo automático de amortización
- ✅ Sistema financiero completo (capital + intereses)
- ✅ Estados dinámicos (Activo/Pagado/Vencido)
- ✅ Seguimiento de progreso de pago
- ✅ Detalles completos con historial

### 💳 Gestión de Pagos
- ✅ Registro manual de cuotas y pagos parciales
- ✅ Cálculo automático capital vs intereses
- ✅ Actualización automática de saldos
- ✅ Validaciones de montos y fechas
- ✅ Historial detallado por cliente/crédito

### 📊 Reportes Profesionales
- ✅ Dashboard con métricas en tiempo real
- ✅ **Gráficos interactivos** (barras, líneas, tortas)
- ✅ Reportes de pagos con filtros avanzados
- ✅ Reportes de clientes morosos
- ✅ **Exportación múltiple**:
  - 📊 **Excel** (.xlsx) con formato profesional
  - 📄 **PDF** con diseño estilizado
  - 📋 **CSV** para análisis de datos
  - 🖨️ **Impresión** con formato optimizado

### ⚙️ Configuración Avanzada
- ✅ 19 configuraciones del sistema por defecto
- ✅ Parámetros financieros (tasas, límites, días de gracia)
- ✅ Configuraciones de notificaciones
- ✅ Gestión visual de parámetros
- ✅ Creación de configuraciones personalizadas

### 🎛️ Dashboard Interactivo
- ✅ Vista general con KPIs clave
- ✅ Estadísticas en tiempo real
- ✅ Gráficas de distribución y tendencias
- ✅ Alertas visuales
- ✅ Navegación intuitiva con menú lateral

## 🛠️ Desarrollo y Configuración

### Ejecutar en Modo Desarrollo
```bash
python main.py
```
La aplicación se ejecuta en `http://127.0.0.1:8000` con **recarga automática** al detectar cambios.

### 📦 Dependencias Principales
```txt
fastapi==0.104.1          # Framework web moderno
uvicorn==0.24.0           # Servidor ASGI
sqlalchemy==2.0.23        # ORM de base de datos
pydantic==2.5.0           # Validación de datos
python-jose[cryptography] # JWT tokens
bcrypt==4.0.1             # Hashing de contraseñas
python-multipart==0.0.6   # Manejo de formularios
pandas==2.1.4             # Análisis de datos para reportes
openpyxl==3.1.2           # Exportación Excel
reportlab==4.0.7          # Generación PDF
chart.js (CDN)            # Gráficos interactivos
```

### 🗄️ Base de Datos
- **Motor**: SQLite (embebido, sin configuración)
- **Archivo**: `instance/sql_app.db`
- **ORM**: SQLAlchemy 2.0 con SQLAlchemy ORM
- **Inicialización**: `python init_db.py`
- **Datos de ejemplo**: `python create_prestamos_table.py`

### 🔧 Variables de Entorno (.env)
```env
# Base de datos
DATABASE_URL=sqlite:///./instance/sql_app.db

# Seguridad
SECRET_KEY=tu_clave_ultra_secreta_aqui_32_caracteres_min
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Aplicación
DEBUG=true
APP_NAME=Credexa
EMPRESA_NOMBRE=Tu Empresa

# Configuración adicional (opcional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=tu@email.com
```

## 📈 Características Técnicas

### 🔒 Seguridad
- ✅ **Autenticación JWT** con expiración automática
- ✅ **Hashing bcrypt** para contraseñas
- ✅ **Validaciones Pydantic** en todas las entradas
- ✅ **Protección CSRF** implícita
- ✅ **Control de acceso basado en roles**

### ⚡ Rendimiento
- ✅ **Base de datos embebida** (SQLite)
- ✅ **Lazy loading** optimizado
- ✅ **Consultas eficientes** con joins apropiados
- ✅ **Caché automático** de templates Jinja2
- ✅ **Compresión gzip** automática

### 🎨 Interfaz de Usuario
- ✅ **Responsive design** con Bootstrap 5
- ✅ **Interactividad HTMX** sin JavaScript complejo
- ✅ **Componentes reutilizables** con Jinja2
- ✅ **Feedback visual** en tiempo real
- ✅ **Accesibilidad WCAG** básica

### 📊 Reportes Avanzados
- ✅ **Exportación Excel** con formato condicional
- ✅ **PDF profesional** con ReportLab
- ✅ **CSV optimizado** para análisis
- ✅ **Impresión web** con CSS especial
- ✅ **Gráficos Chart.js** interactivos

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Para contribuir:

1. 🍴 **Fork** el proyecto
2. 🌿 Crear una rama: `git checkout -b feature/nueva-funcionalidad`
3. 💻 Implementar cambios
4. ✅ Crear tests si es necesario
5. 📝 **Commit**: `git commit -m 'Agrega nueva funcionalidad'`
6. 📤 **Push**: `git push origin feature/nueva-funcionalidad`
7. 🔄 Crear **Pull Request**

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico o reportar bugs:

- 📧 **Email**: soporte@credexa.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/usuario/credexa/issues)
- 📚 **Documentación**: `http://127.0.0.1:8000/docs`

---

## 🎉 ¡Credexa Listo para Producción!

**Credexa es un sistema completo y profesional para la gestión financiera de pequeñas empresas, desarrollado con las mejores prácticas de desarrollo web moderno.**

### 🚀 Características Destacadas:
- ✅ **100% funcional** - Todos los módulos implementados
- ✅ **Interfaz profesional** - Diseño moderno y responsivo
- ✅ **Reportes avanzados** - Exportación múltiple y gráficos
- ✅ **Seguridad robusta** - JWT + bcrypt + validaciones
- ✅ **Código mantenible** - Arquitectura modular y documentada
- ✅ **Base de datos embebida** - SQLite sin configuración
- ✅ **Desarrollo rápido** - Hot reload y debugging

### 📞 ¿Necesitas ayuda?
- 📖 Lee la documentación completa en `/docs`
- 🎯 Explora las funcionalidades desde el dashboard
- ⚙️ Configura parámetros en la sección de configuración

---

**Desarrollado con ❤️ para potenciar pequeñas empresas con tecnología moderna**
