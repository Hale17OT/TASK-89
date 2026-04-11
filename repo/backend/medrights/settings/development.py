"""Development settings - local use only."""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use simpler logging in development
LOGGING["formatters"]["json"] = {  # noqa: F405
    "format": "%(levelname)s %(name)s %(message)s",
}

# Allow browsable API in development
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
