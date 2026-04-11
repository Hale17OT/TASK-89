"""
Base settings for MedRights Patient Media & Consent Portal.
All environment-specific settings override from this base.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Tenancy Model
# ---------------------------------------------------------------------------
# MedRights is a single-tenant, single-clinic system deployed on-premises.
# All data belongs to one organizational entity. There is no multi-tenant
# isolation layer because the system runs on a dedicated local server per
# clinic. Access control is enforced via role-based permissions (RBAC),
# not tenant scoping. This is an intentional architectural decision
# aligned with the offline, single-clinic deployment model.
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "MEDRIGHTS_SECRET_KEY",
    "django-insecure-dev-only-key-never-use-in-production",
)

DEBUG = False

ALLOWED_HOSTS = os.environ.get("MEDRIGHTS_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_celery_beat",
    # Project apps
    "apps.accounts",
    "apps.mpi",
    "apps.consent",
    "apps.media_engine",
    "apps.financials",
    "apps.audit",
    "apps.reports",
    "apps.health",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "infrastructure.middleware.request_id.RequestIDMiddleware",
    "infrastructure.middleware.encryption_context.EncryptionContextMiddleware",
    "infrastructure.middleware.session_timeout.SessionTimeoutMiddleware",
    "infrastructure.middleware.throttle.WorkstationThrottleMiddleware",
    "infrastructure.middleware.sudo_mode.SudoModeMiddleware",
    "infrastructure.middleware.audit_logging.AuditLoggingMiddleware",
]

ROOT_URLCONF = "medrights.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "medrights.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DATABASE_NAME", "medrights"),
        "USER": os.environ.get("DATABASE_USER", "medrights_app"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "medrights_app_pass"),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "3306"),
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "medrights_session"
SESSION_COOKIE_AGE = 28800  # 8 hours absolute maximum
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # LAN-only offline system; set True if TLS added
SESSION_SAVE_EVERY_REQUEST = True

# Custom session timeout settings
MEDRIGHTS_IDLE_TIMEOUT_SECONDS = 900  # 15 minutes
MEDRIGHTS_ABSOLUTE_SESSION_LIMIT = 28800  # 8 hours

# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
CSRF_COOKIE_HTTPONLY = False  # JS must read the CSRF token
CSRF_COOKIE_NAME = "medrights_csrf"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# ---------------------------------------------------------------------------
# Throttling
# ---------------------------------------------------------------------------
MEDRIGHTS_MAX_FAILED_LOGINS = 5
MEDRIGHTS_FAILED_LOGIN_WINDOW_SECONDS = 600  # 10 minutes
MEDRIGHTS_LOCKOUT_DURATION_SECONDS = 600  # 10 minutes
MEDRIGHTS_LOCKOUTS_BEFORE_BLACKLIST = 3
MEDRIGHTS_BLACKLIST_WINDOW_SECONDS = 86400  # 24 hours

# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------
MEDRIGHTS_MASTER_KEY = os.environ.get("MEDRIGHTS_MASTER_KEY", "")

# ---------------------------------------------------------------------------
# File uploads
# ---------------------------------------------------------------------------
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB, above this uses temp file
MEDIA_ROOT = os.path.join(BASE_DIR, "storage")
MEDRIGHTS_STORAGE_ROOT = os.environ.get(
    "MEDRIGHTS_STORAGE_ROOT", os.path.join(BASE_DIR, "storage")
)

# ---------------------------------------------------------------------------
# Timezone & Internationalization
# ---------------------------------------------------------------------------
USE_TZ = True
TIME_ZONE = "UTC"
CLINIC_TIMEZONE = os.environ.get("CLINIC_TIMEZONE", "America/New_York")
LANGUAGE_CODE = "en-us"
USE_I18N = False

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "infrastructure.exceptions.custom_exception_handler",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "120/minute",
    },
}

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 600

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "infrastructure.logging.formatter.JSONLogFormatter",
        },
        "simple": {
            "format": "%(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "medrights": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "medrights.auth": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "medrights.audit": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "medrights.financials": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
