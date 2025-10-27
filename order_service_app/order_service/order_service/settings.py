from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
import pymysql

# -------------------------------------------------------------------
# Base directory & load environment variables
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# -------------------------------------------------------------------
# MySQL driver
# -------------------------------------------------------------------
pymysql.install_as_MySQLdb()

# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
USE_X_FORWARDED_HOST = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "orders": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "formatters": {
    "verbose": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
},
"handlers": {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "verbose",
    },
},
    },
}




# -------------------------------------------------------------------
# Installed Apps
# -------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "django_extensions",

    # Local apps
    "apps.orders",
]


# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------------------------------------------------------
# URL / WSGI
# -------------------------------------------------------------------
ROOT_URLCONF = "order_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "order_service.wsgi.application"

# -------------------------------------------------------------------
# Database (MySQL)
# -------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "order_service_db"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# -------------------------------------------------------------------
# Django REST Framework & JWT Authentication
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "secret")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_LIFETIME", 5))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_LIFETIME", 1))),
    "SIGNING_KEY": os.getenv("JWT_SECRET_KEY", SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# -------------------------------------------------------------------
# Orders app models
# -------------------------------------------------------------------
# No custom user model here; we only store user_id as integer from user_service

# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static files
# -------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------------------------------------------------
# Default primary key
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
