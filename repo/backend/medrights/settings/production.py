"""Production settings - used in Docker containers."""
import base64 as _b64
import logging
import os

from .base import *  # noqa: F401, F403

DEBUG = False

_logger = logging.getLogger("medrights")

# -- Secret key validation --
_secret = os.environ.get("MEDRIGHTS_SECRET_KEY", "")
if _secret == "django-insecure-dev-only-key-never-use-in-production" or not _secret:
    raise ValueError("MEDRIGHTS_SECRET_KEY environment variable must be set")

# -- Master encryption key validation (must be valid base64, >= 32 bytes) --
_master_key_raw = os.environ.get("MEDRIGHTS_MASTER_KEY", "")
if not _master_key_raw:
    raise ValueError("MEDRIGHTS_MASTER_KEY environment variable must be set")
try:
    _decoded = _b64.b64decode(_master_key_raw)
    if len(_decoded) < 32:
        raise ValueError(
            f"MEDRIGHTS_MASTER_KEY must decode to >= 32 bytes (got {len(_decoded)}). "
            "Generate: python3 -c \"import base64,os; print(base64.b64encode(os.urandom(32)).decode())\""
        )
except ValueError:
    raise
except Exception as _exc:
    raise ValueError(f"MEDRIGHTS_MASTER_KEY is not valid base64: {_exc}") from _exc
