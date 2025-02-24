"""
Django settings for tbk project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
import environ

# Inicializar el objeto de entorno
env = environ.Env()
# Especificar explícitamente la ruta al archivo .env
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# Leer el archivo .env
env.read_env(env_file)
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
ALLOWED_HOSTS = ['tbkdesire.cl', 'www.tbkdesire.cl', '127.0.0.1','localhost','147.93.67.92']
LOGIN_URL = '/web/login/'  # Asegúrate de que esta URL esté definida
LOGIN_REDIRECT_URL = '/web/'  # Página a la que se redirige después del login
LOGOUT_REDIRECT_URL = '/web/'  # Página a la que se redirige después del logout
# Application definition

INSTALLED_APPS = [
    "web",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
]

# Para el manejo de archivos de medios
STATIC_URL = '/static/'
STATIC_ROOT='/var/www/tbk/staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/tbk/media'


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tbk.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tbk.wsgi.application"
# Ahora puedes usar las variables de entorno en tus configuraciones
# Configuración de la clave secreta
SECRET_KEY = env('SECRET_KEY')  # Cargar desde el archivo .env

# Modo debug (es mejor no dejar DEBUG=True en producción)
DEBUG = True

# Configuración de la base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME'),  # Cargar desde .env
        'USER': env('DATABASE_USER'),  # Cargar desde .env
        'PASSWORD': env('DATABASE_PASSWORD'),  # Cargar desde .env
        'HOST': env('DATABASE_HOST', default='localhost'),  # Valor predeterminado para el host
        'PORT': env.int('DATABASE_PORT', default=5432),  # Usar .int() para el puerto
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "es-cl"  # Español de Chile

TIME_ZONE = "Chile/Continental"  # Zona horaria de Chile

USE_I18N = True

USE_TZ = True



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_USE_TLS = True  # True para TLS, False para SSL (según el servidor SMTP)


# Cargar las variables de MercadoPago
MERCADOPAGO_ACCESS_TOKEN = env('MERCADOPAGO_ACCESS_TOKEN')
MERCADOPAGO_PUBLIC_KEY = env('MERCADOPAGO_PUBLIC_KEY')


from django.core.exceptions import ImproperlyConfigured


# Forzar UTF-8 en lugar de ASCII para emails
from email import charset
charset.add_charset('utf-8', charset.SHORTEST, charset.QP, 'utf-8')

# Configuración de correo SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')  # Valor predeterminado en caso de que no esté en .env
EMAIL_PORT = env.int('EMAIL_PORT', default=587)  # Usamos .int() para convertirlo a un número
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)  # .bool() para valores booleanos
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)  # .bool() para valores booleanos

EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# Validación de configuración crítica
def validate_email_settings():
    required_settings = [
        ('EMAIL_HOST_USER', EMAIL_HOST_USER),
        ('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD),
        ('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL),
    ]
    
    for setting_name, setting_value in required_settings:
        if not setting_value:
            raise ImproperlyConfigured(
                f"La variable de entorno {setting_name} no está configurada. "
                "Es necesaria para el funcionamiento del email."
            )

# Ejecutar validación al inicio
validate_email_settings()
