"""
Django settings for imet project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY', 'mc7!^g8_bn%*!8ik=p=z=rxoymf$zg$t9%*kjnus2cds4o!e6n')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED HOSTS
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# CONFIGURACIÓN DE LOGIN
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# CSRF - Solo en producción
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        'https://la-guarida-de-timon.com',
        'https://www.la-guarida-de-timon.com',
    ]
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# INSTALLED APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "widget_tweaks",
    'entidad',
    'channels', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'imet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'imet.wsgi.application'
ASGI_APPLICATION = 'imet.asgi.application'

# DATABASE - Configuración flexible
if DEBUG:
    # Base de datos LOCAL (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Base de datos PRODUCCIÓN (MySQL/MariaDB)
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DATABASE_ENGINE', 'django.db.backends.mysql'),
            'NAME': os.getenv('DATABASE_NAME', 'imet_ventas'),
            'USER': os.getenv('DATABASE_USER', 'imet_user'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', 'Timonymumba.2025'),
            'HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'PORT': os.getenv('DATABASE_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'use_unicode': True,
            },
        }
    }

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# CHANNELS
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# INTERNATIONALIZATION
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'static']

# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DEFAULT PRIMARY KEY
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGGING (solo en producción)
if not DEBUG:
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }

# IMPRESORA TÉRMICA - MODO PRUEBA
THERMAL_PRINTER = {
    'type': 'file',
    'paper_width': 58,
    # Guardar en la carpeta del proyecto (más confiable)
    'output_path': os.path.join(BASE_DIR, 'thermal_print.bin'),
}

# Cuando tengas la impresora física, cambia a:
# THERMAL_PRINTER = {
#     'type': 'usb',
#     'paper_width': 58,
#     'vendor_id': 0x04b8,
#     'product_id': 0x0e15,
# }