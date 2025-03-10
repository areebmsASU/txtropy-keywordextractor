from pathlib import Path
from os import environ

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-7r16g054-%0pyv0267nz3dddw^jvw60ht-7c=iz@ixbsf7ad%)"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["corsheaders", "gutenberg.apps.GutenbergConfig"]

ROOT_URLCONF = "keywordextractor.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "keywordextractor",
        "PORT": 5432,
        "HOST": environ.get("DB_HOST"),
        "USER": environ.get("DB_USER"),
        "PASSWORD": environ.get("DB_PASSWORD"),
    }
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery settings
CELERY_BROKER_URL = "redis://localhost:6379/0"
