"""Testing settings - used by pytest."""
from .base import *  # noqa: F401, F403

DEBUG = False

# Use SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# Celery runs tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Simpler password hashing for test speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable password validators in tests
AUTH_PASSWORD_VALIDATORS = []

# Use simple logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# Test encryption key (32 bytes base64)
MEDRIGHTS_MASTER_KEY = "dGVzdGluZy1rZXktMzItYnl0ZXMtbG9uZw=="

MEDRIGHTS_STORAGE_ROOT = "/tmp/medrights_test_storage"
