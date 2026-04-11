"""Unit tests for the client-error log redaction pipeline.

Tests each redaction layer independently, plus strict mode behaviour,
to ensure CI catches regressions in PII/secret scrubbing.
"""
import pytest

# Django must be configured before importing application modules.
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _setup_django():
    """Ensure Django settings are loaded."""
    import django
    django.setup()


# ── Imports (after Django setup) ────────────────────────────────────────

def _get_fns():
    from apps.audit.views_client_logs import (
        _deep_redact_text,
        _minimise_stack,
        _redact_kv_pairs,
        _redact_sensitive_values,
        _redact_url,
        _sanitize_extra_deep,
        _redact_high_entropy,
    )
    return {
        "deep": _deep_redact_text,
        "stack": _minimise_stack,
        "kv": _redact_kv_pairs,
        "pattern": _redact_sensitive_values,
        "url": _redact_url,
        "extra": _sanitize_extra_deep,
        "entropy": _redact_high_entropy,
    }


# ── Pattern redaction ───────────────────────────────────────────────────

class TestPatternRedaction:
    def test_ssn_dashed(self):
        fn = _get_fns()["pattern"]
        assert "123-45-6789" not in fn("SSN: 123-45-6789")
        assert "[REDACTED_SSN]" in fn("SSN: 123-45-6789")

    def test_email(self):
        fn = _get_fns()["pattern"]
        assert "user@example.com" not in fn("Contact user@example.com")

    def test_mrn(self):
        fn = _get_fns()["pattern"]
        assert "MRN-12345" not in fn("Patient MRN-12345")
        assert "MRN: 99999" not in fn("MRN: 99999")

    def test_phone(self):
        fn = _get_fns()["pattern"]
        assert "555-123-4567" not in fn("Call 555-123-4567")

    def test_credit_card(self):
        fn = _get_fns()["pattern"]
        assert "4111-1111-1111-1111" not in fn("CC 4111-1111-1111-1111")

    def test_jwt(self):
        fn = _get_fns()["pattern"]
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        assert jwt not in fn(f"Token: {jwt}")

    def test_bearer(self):
        fn = _get_fns()["pattern"]
        assert "sk-abc123" not in fn("Bearer sk-abc123")

    def test_hex_long(self):
        fn = _get_fns()["pattern"]
        h = "a" * 32
        assert h not in fn(f"Hash {h}")

    def test_dob_pattern(self):
        fn = _get_fns()["pattern"]
        assert fn("dob=1990-01-01") == "[REDACTED_DOB]"

    def test_normal_error_preserved(self):
        fn = _get_fns()["pattern"]
        msg = "TypeError: Cannot read properties of undefined"
        assert fn(msg) == msg


# ── KV catch-all ────────────────────────────────────────────────────────

class TestKVRedaction:
    def test_long_value_redacted(self):
        fn = _get_fns()["kv"]
        result = fn(" auth_token=sk_live_abc123def456ghi789")
        assert "sk_live_abc123def456ghi789" not in result

    def test_short_value_preserved(self):
        fn = _get_fns()["kv"]
        # short value (< 9 chars) not caught by kv
        result = fn(" status=active")
        assert "active" in result

    def test_safe_kv_preserved(self):
        fn = _get_fns()["kv"]
        result = fn(" enabled=undefined")
        assert "undefined" in result


# ── Entropy detection ───────────────────────────────────────────────────

class TestEntropyRedaction:
    def test_high_entropy_token_redacted(self):
        fn = _get_fns()["entropy"]
        token = "xK9mZp3qR7wL2vN8bY1jT6hA"
        result = fn(f"session {token}")
        assert token not in result

    def test_low_entropy_word_preserved(self):
        fn = _get_fns()["entropy"]
        result = fn("aaaaaaaaaaaaaaaaaaaaaaaaa")
        assert "aaaaaaaaaaaaaaaaaaaaaaaaa" in result

    def test_redaction_placeholder_not_double_redacted(self):
        fn = _get_fns()["entropy"]
        result = fn("[REDACTED_SSN] some text")
        assert "[REDACTED_SSN]" in result


# ── Stack minimiser ─────────────────────────────────────────────────────

class TestStackMinimiser:
    def test_chrome_frames_extracted(self):
        fn = _get_fns()["stack"]
        stack = (
            "TypeError: Cannot read properties of null\n"
            "    at UserProfile.render (components/UserProfile.tsx:45:12)\n"
            "    at renderWithHooks (react-dom.development.js:14985:18)\n"
        )
        result = fn(stack)
        assert "at UserProfile.render (components/UserProfile.tsx:45:12)" in result
        assert "Cannot read properties" not in result

    def test_firefox_frames_extracted(self):
        fn = _get_fns()["stack"]
        result = fn("render@components/UserProfile.tsx:45:12")
        assert "at render (components/UserProfile.tsx:45:12)" in result

    def test_pii_in_error_message_dropped(self):
        fn = _get_fns()["stack"]
        stack = (
            "Error: Failed to load patient SSN: 123-45-6789\n"
            "    at fetchPatient (api/patients.ts:30:5)\n"
        )
        result = fn(stack)
        assert "123-45-6789" not in result
        assert "at fetchPatient (api/patients.ts:30:5)" in result

    def test_embedded_data_dropped(self):
        fn = _get_fns()["stack"]
        stack = (
            '    at handleClick (Button.tsx:12:8)\n'
            '    user data: {"name": "John Doe", "mrn": "MRN-12345"}\n'
            '    at App (App.tsx:5:1)\n'
        )
        result = fn(stack)
        assert "John Doe" not in result
        assert "MRN-12345" not in result
        assert "at handleClick (Button.tsx:12:8)" in result
        assert "at App (App.tsx:5:1)" in result

    def test_frame_cap(self):
        fn = _get_fns()["stack"]
        stack = "\n".join(f"    at func{i} (file.js:{i}:1)" for i in range(50))
        result = fn(stack)
        assert result.count("at func") == 20


# ── URL redaction ───────────────────────────────────────────────────────

class TestURLRedaction:
    def test_sensitive_param_redacted(self):
        fn = _get_fns()["url"]
        result = fn("https://app.com/page?token=abc123&page=1")
        assert "abc123" not in result
        assert "page=1" in result

    def test_multiple_params_redacted(self):
        fn = _get_fns()["url"]
        result = fn("https://app.com/?token=x&ssn=y&page=2")
        assert "x" not in result.split("token=")[1].split("&")[0]
        assert "y" not in result.split("ssn=")[1].split("&")[0]


# ── Extra dict sanitization ─────────────────────────────────────────────

class TestExtraSanitization:
    def test_sensitive_keys_stripped(self):
        fn = _get_fns()["extra"]
        result = fn({"password": "secret", "component": "Login"})
        assert "password" not in result
        assert result["component"] == "Login"

    def test_key_cap(self):
        fn = _get_fns()["extra"]
        result = fn({f"key_{i}": f"v{i}" for i in range(20)})
        assert len(result) <= 10

    def test_value_length_cap(self):
        fn = _get_fns()["extra"]
        result = fn({"note": "x" * 1000})
        assert len(result["note"]) <= 500

    def test_nested_flattened(self):
        fn = _get_fns()["extra"]
        result = fn({"nested": {"a": "b"}})
        assert isinstance(result["nested"], str)

    def test_numeric_preserved(self):
        fn = _get_fns()["extra"]
        result = fn({"count": 42})
        assert result["count"] == "42"

    def test_values_redacted(self):
        fn = _get_fns()["extra"]
        result = fn({"note": "Patient SSN is 123-45-6789"})
        assert "123-45-6789" not in result["note"]


# ── Deep redact pipeline (integration) ──────────────────────────────────

class TestDeepRedactPipeline:
    def test_combined_pipeline(self):
        fn = _get_fns()["deep"]
        text = "Error for user@example.com with token=sk_live_abc123def456ghi789 and SSN 123-45-6789"
        result = fn(text)
        assert "user@example.com" not in result
        assert "sk_live_abc123def456ghi789" not in result
        assert "123-45-6789" not in result

    def test_normal_message_survives(self):
        fn = _get_fns()["deep"]
        msg = "TypeError: Cannot read properties of undefined"
        assert fn(msg) == msg


# ── Strict mode ─────────────────────────────────────────────────────────

class TestStrictMode:
    """Tests for CLIENT_LOG_STRICT_MODE=True behaviour."""

    def test_strict_rejects_extra_field(self, client):
        """In strict mode, the 'extra' field is not in the allowlist."""
        from django.test import override_settings

        with override_settings(
            CLIENT_LOG_STRICT_MODE=True,
            CSRF_TRUSTED_ORIGINS=["http://testserver"],
        ):
            from rest_framework.test import APIClient
            c = APIClient()
            resp = c.post(
                "/api/v1/logs/client-errors/",
                {
                    "message": "TypeError: something broke",
                    "level": "error",
                    "extra": {"debug": "value"},
                },
                format="json",
                HTTP_ORIGIN="http://testserver",
            )
            assert resp.status_code == 400
            assert "extra" in resp.data.get("message", "").lower()

    def test_strict_truncates_message_to_error_type(self, client):
        """In strict mode, message is reduced to the JS error type prefix."""
        from django.test import override_settings

        with override_settings(
            CLIENT_LOG_STRICT_MODE=True,
            CSRF_TRUSTED_ORIGINS=["http://testserver"],
        ):
            from rest_framework.test import APIClient
            c = APIClient()
            resp = c.post(
                "/api/v1/logs/client-errors/",
                {
                    "message": "TypeError: Cannot read properties of undefined (reading 'name')",
                    "level": "error",
                },
                format="json",
                HTTP_ORIGIN="http://testserver",
            )
            assert resp.status_code == 201

    def test_non_strict_allows_extra(self, client):
        """In non-strict mode, 'extra' is allowed."""
        from django.test import override_settings

        with override_settings(
            CLIENT_LOG_STRICT_MODE=False,
            CSRF_TRUSTED_ORIGINS=["http://testserver"],
        ):
            from rest_framework.test import APIClient
            c = APIClient()
            resp = c.post(
                "/api/v1/logs/client-errors/",
                {
                    "message": "TypeError: something broke",
                    "level": "error",
                    "extra": {"component": "LoginForm"},
                },
                format="json",
                HTTP_ORIGIN="http://testserver",
            )
            assert resp.status_code == 201
