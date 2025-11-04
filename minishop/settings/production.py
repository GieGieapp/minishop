# minishop/settings/production.py
from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if os.environ.get("DJANGO_ALLOWED_HOSTS") else []

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "minishop"),
        "USER": os.environ.get("PGUSER", ""),
        "PASSWORD": os.environ.get("PGPASSWORD", ""),
        "HOST": os.environ.get("PGHOST", "127.0.0.1"),
        "PORT": os.environ.get("PGPORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
