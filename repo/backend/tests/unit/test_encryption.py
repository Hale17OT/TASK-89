"""Unit tests for the EncryptionService."""
import base64

import pytest

from infrastructure.encryption.service import EncryptionService


@pytest.fixture
def svc():
    """Return a freshly initialised EncryptionService instance."""
    service = EncryptionService()
    key = base64.b64encode(b"test-key-32-bytes-long-xxxxxxxx").decode()
    service.initialize(key)
    return service


@pytest.fixture
def uninitialised_svc():
    """Return an EncryptionService that has NOT been initialised."""
    return EncryptionService()


# ------------------------------------------------------------------
# Encrypt / Decrypt
# ------------------------------------------------------------------

class TestEncryptDecrypt:
    def test_encrypt_decrypt_roundtrip(self, svc):
        plaintext = "sensitive patient data"
        ciphertext = svc.encrypt_aes_gcm(plaintext)
        result = svc.decrypt_aes_gcm(ciphertext)
        assert result == plaintext

    def test_encrypt_produces_different_ciphertext(self, svc):
        """AES-GCM uses a random nonce so the same plaintext must produce
        different ciphertext on each call."""
        plaintext = "same input"
        ct1 = svc.encrypt_aes_gcm(plaintext)
        ct2 = svc.encrypt_aes_gcm(plaintext)
        assert ct1 != ct2

    def test_encrypt_decrypt_empty_string(self, svc):
        ciphertext = svc.encrypt_aes_gcm("")
        assert svc.decrypt_aes_gcm(ciphertext) == ""

    def test_encrypt_decrypt_unicode(self, svc):
        plaintext = "Nombre del paciente"
        ciphertext = svc.encrypt_aes_gcm(plaintext)
        assert svc.decrypt_aes_gcm(ciphertext) == plaintext


# ------------------------------------------------------------------
# HMAC
# ------------------------------------------------------------------

class TestHMAC:
    def test_compute_hmac_deterministic(self, svc):
        """The same input must always produce the same HMAC."""
        h1 = svc.compute_hmac("patient-mrn-123")
        h2 = svc.compute_hmac("patient-mrn-123")
        assert h1 == h2

    def test_compute_hmac_different_inputs(self, svc):
        h1 = svc.compute_hmac("input-a")
        h2 = svc.compute_hmac("input-b")
        assert h1 != h2


# ------------------------------------------------------------------
# Masking
# ------------------------------------------------------------------

class TestMasking:
    def test_mask_ssn(self, svc):
        assert svc.mask_value("123456789", mask_type="ssn") == "***-**-6789"

    def test_mask_name(self, svc):
        assert svc.mask_value("John", mask_type="name") == "J***"

    def test_mask_short_value(self, svc):
        """A single character name masks to '*'."""
        assert svc.mask_value("J", mask_type="name") == "*"


# ------------------------------------------------------------------
# Subkey derivation
# ------------------------------------------------------------------

class TestSubkeyDerivation:
    def test_derive_subkey_stable(self, svc):
        k1 = svc.derive_subkey("encryption")
        k2 = svc.derive_subkey("encryption")
        assert k1 == k2

    def test_derive_subkey_different_purposes(self, svc):
        k1 = svc.derive_subkey("encryption")
        k2 = svc.derive_subkey("hmac")
        assert k1 != k2


# ------------------------------------------------------------------
# Uninitialised service
# ------------------------------------------------------------------

class TestUninitialisedService:
    def test_uninitialized_service_raises(self, uninitialised_svc):
        with pytest.raises(RuntimeError, match="not initialized"):
            uninitialised_svc.encrypt_aes_gcm("data")
