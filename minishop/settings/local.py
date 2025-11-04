from .base import *
DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}
