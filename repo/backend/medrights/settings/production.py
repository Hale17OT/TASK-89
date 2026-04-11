"""Production settings - used in Docker containers."""
import os

from .base import *  # noqa: F401, F403

DEBUG = False

# Ensure secret key is set from environment
assert SECRET_KEY != "django-insecure-dev-only-key-never-use-in-production", (  # noqa: F405
    "MEDRIGHTS_SECRET_KEY environment variable must be set in production"
)

# Reject weak/missing master encryption key
import base64 as _b64
_master_key_raw = os.environ.get("MEDRIGHTS_MASTER_KEY", "")
if _master_key_raw in ("", "dGhpcyBpcyBhIDMyIGJ5dGUga2V5IGZvciBkZXY="):
    raise ValueError("MEDRIGHTS_MASTER_KEY must be set to a strong, unique value")
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
