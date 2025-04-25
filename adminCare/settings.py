import os
from pathlib import Path
from datetime import timedelta    # seguirá siendo útil pronto

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'clave_por_defecto_segura')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [
    'admincare.onrender.com',
    '127.0.0.1',
    'localhost',
]

# ————————————————————————————————
# Apps
# ————————————————————————————————
INSTALLED_APPS = [
    'django_cleanup.apps.CleanupConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # terceros
    'storages',               # django‑storages
    # propios
    'appAdminCare',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'adminCare.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'adminCare.wsgi.application'

# ————————————————————————————————
# Base de datos (SQLite → dev)
# ————————————————————————————————
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ————————————————————————————————
# Autenticación / i18n
# ————————————————————————————————
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

# ————————————————————————————————
# Archivos estáticos
# ————————————————————————————————
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

USE_S3 = os.getenv('USE_S3') == 'True'

if USE_S3:
    # ---------- S3 ----------
    AWS_ACCESS_KEY_ID       = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY   = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME      = os.getenv('AWS_S3_REGION_NAME', 'eu-west-3')
    AWS_S3_ADDRESSING_STYLE = os.getenv('AWS_S3_ADDRESSING_STYLE', 'virtual')

    # Config recomendada por django-storages
    AWS_DEFAULT_ACL           = None
    AWS_S3_FILE_OVERWRITE     = False
    AWS_QUERYSTRING_AUTH      = True
    AWS_S3_SIGNATURE_VERSION  = 's3v4'

    # Usa manifest para cache busting
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3ManifestStaticStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    # ---------- local (Whitenoise) ----------
    from whitenoise.storage import CompressedManifestStaticFilesStorage
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

