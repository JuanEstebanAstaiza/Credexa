# Credexa - Sistema de Gestión Financiera

Aplicación web de uso local para la gestión de préstamos de pequeñas empresas, desarrollada con FastAPI y SQLite.

## Características

### Módulo de Autenticación y Usuarios ✅
- ✅ Login de empleados (administrador y digitadores)
- ✅ Roles y permisos básicos
- ✅ Recuperación de contraseña
- ✅ Sistema de tokens JWT
- ✅ Interfaz web moderna con Bootstrap y HTMX

### Próximos Módulos
- 📋 Módulo de Clientes
- 💰 Módulo de Créditos
- 💳 Módulo de Pagos
- 📊 Módulo de Reportes
- 🎛️ Panel de Control (Dashboard)
- ⚙️ Configuración Básica

## Tecnologías Utilizadas

- **Backend**: FastAPI
- **Base de Datos**: SQLite (embebida)
- **ORM**: SQLAlchemy
- **Autenticación**: JWT Tokens
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **UI Framework**: Bootstrap 5
- **Interactividad**: HTMX
- **Iconos**: Font Awesome

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   # Si clonaste el repositorio
   cd GestionPrestamos
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicializar la base de datos**
   ```bash
   python init_db.py
   ```

4. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

5. **Acceder a la aplicación**
   - Abrir el navegador en: `http://127.0.0.1:8000`
   - Usuario por defecto: `admin`
   - Contraseña por defecto: `admin123`

## Usuarios Iniciales

Después de ejecutar `init_db.py`, se crean los siguientes usuarios:

### Administrador
- **Usuario**: admin
- **Contraseña**: admin123
- **Email**: admin@prestamos.com
- **Rol**: Administrador

### Digitador
- **Usuario**: digitador
- **Contraseña**: digitador123
- **Email**: digitador@prestamos.com
- **Rol**: Digitador

## Estructura del Proyecto

```
GestionPrestamos/
├── main.py                 # Punto de entrada de la aplicación
├── init_db.py             # Script de inicialización de BD
├── requirements.txt       # Dependencias del proyecto
├── README.md              # Este archivo
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api.py         # Router principal de la API
│   │   └── auth.py        # Endpoints de autenticación
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py      # Configuración de la aplicación
│   │   ├── database.py    # Configuración de base de datos
│   │   └── security.py    # Utilidades de seguridad y JWT
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py        # Modelos de Usuario y Rol
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py        # Esquemas Pydantic
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css  # Estilos personalizados
│   │   └── js/
│   │       └── app.js     # JavaScript de la aplicación
│   └── templates/
│       ├── base.html      # Template base
│       ├── dashboard.html # Dashboard principal
│       └── auth/
│           └── login.html # Página de login
├── instance/              # Directorio para archivos de instancia
└── .env                   # Variables de entorno (opcional)
```

## Uso de la Aplicación

### Acceso
1. Abrir `http://127.0.0.1:8000` en el navegador
2. Iniciar sesión con las credenciales proporcionadas
3. Acceder al dashboard principal

### API Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## Funcionalidades Implementadas

### Autenticación
- ✅ Login con usuario/contraseña
- ✅ Validación de credenciales
- ✅ Sistema de tokens JWT
- ✅ Protección de rutas
- ✅ Cierre de sesión
- ✅ Recordar sesión (cookies)

### Gestión de Usuarios
- ✅ Roles predefinidos (Admin, Digitador)
- ✅ Creación de usuarios (solo admin)
- ✅ Actualización de usuarios (solo admin)
- ✅ Eliminación de usuarios (solo admin)
- ✅ Listado de usuarios (solo admin)

### Interfaz de Usuario
- ✅ Diseño responsivo con Bootstrap
- ✅ Interactividad con HTMX
- ✅ Dashboard con estadísticas
- ✅ Navegación intuitiva
- ✅ Mensajes de feedback
- ✅ Loading states

## Próximas Funcionalidades

### Módulo de Clientes
- Registro de clientes (nombre, cédula, contacto)
- Edición/actualización de datos
- Listado con búsqueda y filtros
- Historial por cliente

### Módulo de Créditos
- Creación de préstamos (monto, plazo, interés, fecha)
- Estados del préstamo (activo, pagado, en mora)
- Cálculo automático de cuotas
- Opción de refinanciación

### Módulo de Pagos
- Registro manual de pagos
- Actualización automática del saldo
- Historial de pagos
- Validación de mora
- Alertas visuales

### Módulo de Reportes
- Reportes de pagos por fecha
- Clientes en mora
- Exportación a Excel/PDF
- Gráficos y estadísticas

### Dashboard Avanzado
- Vista general completa
- Gráficas interactivas
- Alertas en tiempo real
- Métricas clave

### Configuración
- Parámetros de la empresa
- Tasas de interés predeterminadas
- Días de gracia
- Reglas de negocio

## Desarrollo

### Ejecutar en Modo Desarrollo
```bash
python main.py
```
La aplicación se ejecuta en `http://127.0.0.1:8000` con recarga automática.

### Base de Datos
- **Motor**: SQLite
- **Archivo**: `instance/prestamos.db`
- **ORM**: SQLAlchemy con SQLAlchemy ORM

### Variables de Entorno
Crear un archivo `.env` para configuración personalizada:

```env
DATABASE_URL=sqlite:///./instance/prestamos.db
SECRET_KEY=tu_clave_secreta_aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=true
```

## Contribución

Para contribuir al desarrollo:

1. Hacer fork del proyecto
2. Crear una rama para la nueva funcionalidad
3. Implementar los cambios
4. Crear tests si es necesario
5. Hacer commit y push
6. Crear un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o reportar bugs, por favor contactar al equipo de desarrollo.

---

**Desarrollado con ❤️ para pequeñas empresas de préstamos**
