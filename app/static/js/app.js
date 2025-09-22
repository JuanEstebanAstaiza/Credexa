/**
 * JavaScript personalizado para Credexa - Sistema de Gestión Financiera
 */

// Configuración global
const CONFIG = {
    API_BASE_URL: '/api',
    CSRF_TOKEN: null,
    CURRENT_USER: null
};

// Utilidades generales
const Utils = {
    /**
     * Muestra un mensaje de éxito
     */
    showSuccess: function(message, duration = 5000) {
        this.showAlert(message, 'success', duration);
    },

    /**
     * Muestra un mensaje de error
     */
    showError: function(message, duration = 5000) {
        this.showAlert(message, 'danger', duration);
    },

    /**
     * Muestra un mensaje de advertencia
     */
    showWarning: function(message, duration = 5000) {
        this.showAlert(message, 'warning', duration);
    },

    /**
     * Muestra un mensaje de información
     */
    showInfo: function(message, duration = 5000) {
        this.showAlert(message, 'info', duration);
    },

    /**
     * Muestra una alerta
     */
    showAlert: function(message, type = 'info', duration = 5000) {
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show position-fixed"
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                <i class="fas fa-${this.getAlertIcon(type)}"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', alertHtml);

        // Auto-remover después de la duración especificada
        if (duration > 0) {
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) {
                    alert.remove();
                }
            }, duration);
        }
    },

    /**
     * Obtiene el ícono para el tipo de alerta
     */
    getAlertIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    },

    /**
     * Formatea una fecha
     */
    formatDate: function(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };

        const mergedOptions = { ...defaultOptions, ...options };

        if (typeof date === 'string') {
            date = new Date(date);
        }

        return date.toLocaleDateString('es-ES', mergedOptions);
    },

    /**
     * Formatea un número como moneda
     */
    formatCurrency: function(amount, currency = 'COP') {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    /**
     * Formatea un número con separadores de miles
     */
    formatNumber: function(number, decimals = 0) {
        return new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    },

    /**
     * Confirma una acción con un modal
     */
    confirm: function(message, title = 'Confirmar') {
        return new Promise((resolve) => {
            const modalHtml = `
                <div class="modal fade" id="confirmModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                ${message}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    Cancelar
                                </button>
                                <button type="button" class="btn btn-primary" id="confirmBtn">
                                    Aceptar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHtml);

            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            modal.show();

            document.getElementById('confirmBtn').addEventListener('click', () => {
                modal.hide();
                resolve(true);
            });

            document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
                document.getElementById('confirmModal').remove();
                resolve(false);
            });
        });
    },

    /**
     * Muestra un loading spinner
     */
    showLoading: function(element, text = 'Cargando...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        element.innerHTML = `
            <div class="d-flex justify-content-center align-items-center p-3">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                ${text}
            </div>
        `;
        element.classList.add('loading');
    },

    /**
     * Oculta el loading spinner
     */
    hideLoading: function(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        element.classList.remove('loading');
    },

    /**
     * Hace una petición AJAX
     */
    ajax: async function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };

        const mergedOptions = { ...defaultOptions, ...options };

        // No establecer Content-Type si es FormData (el navegador lo hace automáticamente)
        if (!(mergedOptions.body instanceof FormData)) {
            mergedOptions.headers['Content-Type'] = 'application/json';
        }

        // Agregar token de autenticación si existe
        const token = this.getCookie('access_token');
        if (token) {
            mergedOptions.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch {
                    errorData = { detail: await response.text() || 'Error desconocido' };
                }
                throw new Error(errorData.detail || `Error ${response.status}`);
            }

            // Intentar parsear como JSON, si falla devolver el texto
            try {
                return await response.json();
            } catch {
                return await response.text();
            }
        } catch (error) {
            console.error('Error en petición AJAX:', error);
            throw error;
        }
    },

    /**
     * Obtiene una cookie por nombre
     */
    getCookie: function(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    /**
     * Establece una cookie
     */
    setCookie: function(name, value, days = 7) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    },

    /**
     * Elimina una cookie
     */
    deleteCookie: function(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
    }
};

// Configuración de HTMX
document.addEventListener('DOMContentLoaded', function() {
    // Configurar HTMX para incluir tokens de autenticación
    document.body.addEventListener('htmx:configRequest', function(evt) {
        const token = Utils.getCookie('access_token');
        if (token) {
            evt.detail.headers['Authorization'] = `Bearer ${token}`;
        }
    });

    // Manejar errores de HTMX
    document.body.addEventListener('htmx:responseError', function(evt) {
        const xhr = evt.detail.xhr;
        let message = 'Error desconocido';

        try {
            const response = JSON.parse(xhr.responseText);
            message = response.detail || message;
        } catch (e) {
            // Ignorar errores de parsing
        }

        Utils.showError(message);
    });

    // Manejar respuestas exitosas de HTMX
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const xhr = evt.detail.xhr;

        // Si es una respuesta de redirección (por ejemplo después de login)
        if (xhr.status === 200 && evt.detail.requestConfig.verb === 'post') {
            const contentType = xhr.getResponseHeader('content-type');
            if (contentType && contentType.includes('application/json')) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.access_token) {
                        // Guardar token en cookie para acceso futuro
                        Utils.setCookie('access_token', response.access_token);
                        // Login exitoso
                        Utils.showSuccess('Inicio de sesión exitoso');
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 1000);
                    }
                } catch (e) {
                    // No es JSON, continuar normalmente
                }
            }
        }
    });
});

// Funciones específicas de la aplicación
const App = {
    /**
     * Inicializa la aplicación
     */
    init: function() {
        this.setupEventListeners();
        this.loadUserData();
    },

    /**
     * Configura los event listeners
     */
    setupEventListeners: function() {
        // Logout
        const logoutLinks = document.querySelectorAll('a[href="/logout"]');
        logoutLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                App.logout();
            });
        });

        // Formularios con validación
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!App.validateForm(this)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    },

    /**
     * Carga los datos del usuario actual
     */
    loadUserData: async function() {
        try {
            const userData = await Utils.ajax('/api/auth/me');
            CONFIG.CURRENT_USER = userData;
            this.updateUIForUser(userData);
        } catch (error) {
            // Usuario no autenticado, redirigir a login si estamos en una página protegida
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
    },

    /**
     * Actualiza la UI según el usuario
     */
    updateUIForUser: function(user) {
        // Ocultar/mostrar elementos según permisos
        const adminElements = document.querySelectorAll('[data-admin-only]');
        const digitadorElements = document.querySelectorAll('[data-digitador-only]');

        if (user.is_admin) {
            adminElements.forEach(el => el.style.display = '');
        } else {
            adminElements.forEach(el => el.style.display = 'none');
        }

        digitadorElements.forEach(el => el.style.display = '');
    },

    /**
     * Cierra la sesión del usuario
     */
    logout: async function() {
        try {
            await Utils.ajax('/api/auth/logout', { method: 'POST' });
            Utils.deleteCookie('access_token');
            Utils.showSuccess('Sesión cerrada exitosamente');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        } catch (error) {
            Utils.showError('Error al cerrar sesión');
            // Forzar cierre de sesión en el cliente
            Utils.deleteCookie('access_token');
            window.location.href = '/login';
        }
    },

    /**
     * Valida un formulario
     */
    validateForm: function(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });

        // Validación de email
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        });

        return isValid;
    },

    /**
     * Valida un email
     */
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
};

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Exportar utilidades globalmente
window.Utils = Utils;
window.App = App;
