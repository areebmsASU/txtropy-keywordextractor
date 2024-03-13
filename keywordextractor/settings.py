from pathlib import Path
from os import environ

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-7r16g054-%0pyv0267nz3dddw^jvw60ht-7c=iz@ixbsf7ad%)"

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = ["gutenberg.apps.GutenbergConfig"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "keywordextractor",
        "PORT": 5432,
        "HOST": environ.get("DB_HOST"),
        "USER": environ.get("DB_USER"),
        "PASSWORD": environ.get("DB_PASSWORD"),
    },
    "bookbuilder": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bookbuilder",
        "PORT": 5432,
        "HOST": environ.get("DB_HOST"),
        "USER": environ.get("DB_USER"),
        "PASSWORD": environ.get("DB_PASSWORD"),
    },
}


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
