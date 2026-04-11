"""
Encryption service: AES-256-GCM, HMAC-SHA256, and key derivation.
Master key is loaded from environment variable at startup.
"""
import base64
import hashlib
import hmac
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("medrights")


class EncryptionService:
    """Singleton encryption service using application-managed AES-256 keys."""

    def __init__(self):
        self._master_key: bytes | None = None

    def initialize(self, master_key_b64: str, strict: bool = False) -> None:
        """Initialize with base64-encoded master key.

        Parameters
        ----------
        master_key_b64 : str
            Base64-encoded key bytes.
        strict : bool
            If True (production), require exactly 32 decoded bytes and
            reject weak/short keys.  If False (dev/test), short keys
            are padded via SHA-256.
        """
        if not master_key_b64:
            logger.warning("No master key provided; encryption service inactive")
            return
        try:
            key_bytes = base64.b64decode(master_key_b64)
            if strict and len(key_bytes) < 32:
                raise ValueError(
                    f"Master key must be at least 32 bytes (got {len(key_bytes)}). "
                    "Generate with: python3 -c \"import base64,os; print(base64.b64encode(os.urandom(32)).decode())\""
                )
            if len(key_bytes) < 32:
                # Dev/test fallback: derive 32 bytes from shorter input
                key_bytes = hashlib.sha256(key_bytes).digest()
            self._master_key = key_bytes[:32]
            logger.info("Encryption service initialized (key length: %d bytes)", len(key_bytes))
        except ValueError:
            raise  # Re-raise validation errors
        except Exception:
            logger.exception("Failed to initialize encryption service")

    def is_initialized(self) -> bool:
        return self._master_key is not None

    def derive_subkey(self, purpose: str) -> bytes:
        """HKDF-like subkey derivation for different encryption purposes."""
        if not self._master_key:
            raise RuntimeError("Encryption service not initialized")
        return hashlib.sha256(self._master_key + purpose.encode("utf-8")).digest()

    def encrypt_aes_gcm(self, plaintext: str, purpose: str = "default") -> bytes:
        """Encrypt with AES-256-GCM (randomized -- different ciphertext each time)."""
        key = self.derive_subkey(purpose)
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return nonce + ciphertext  # 12-byte nonce prepended

    def decrypt_aes_gcm(self, data: bytes, purpose: str = "default") -> str:
        """Decrypt AES-256-GCM data (nonce prepended)."""
        key = self.derive_subkey(purpose)
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    def compute_hmac(self, plaintext: str, purpose: str = "hmac") -> str:
        """HMAC-SHA256 for searchable encrypted fields. Returns hex string."""
        key = self.derive_subkey(purpose)
        return hmac.new(key, plaintext.encode("utf-8"), hashlib.sha256).hexdigest()

    def mask_value(self, value: str, mask_type: str = "default") -> str:
        """Mask a value for display. Shows last 4 chars by default."""
        if not value:
            return "****"
        if mask_type == "ssn" and len(value) >= 4:
            return f"***-**-{value[-4:]}"
        if mask_type == "name":
            if len(value) <= 1:
                return "*"
            return value[0] + "*" * (len(value) - 1)
        if len(value) <= 4:
            return "*" * len(value)
        return "*" * (len(value) - 4) + value[-4:]


# Singleton instance
encryption_service = EncryptionService()


def initialize_encryption():
    """Called during Django startup to load the master key from settings."""
    import os
    from django.conf import settings
    master_key = getattr(settings, "MEDRIGHTS_MASTER_KEY", "")
    # Strict mode in production only (not testing or development)
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    strict = "production" in settings_module
    if master_key:
        encryption_service.initialize(master_key, strict=strict)
