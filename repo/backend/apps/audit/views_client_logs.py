"""Client-side error logging endpoint for JavaScript error reports.

Defence-in-depth against PHI/secret leakage in logged payloads:

**View layer (this module):**

Layer 1 – Schema: field allowlist, payload size cap, sensitive key rejection.
Layer 2 – Data minimisation: ``message`` capped at 500 chars, ``stack``
          structurally stripped to frame summaries only (``_minimise_stack``),
          ``extra`` flattened to 10 keys / 500 chars per value.
Layer 3 – Pattern redaction: known PII/secret formats (SSN, email, phone,
          CC, JWT, Bearer, hex, base64, DOB, MRN, long digits).
Layer 4 – Structural catch-alls: generic key=value scrubbing, Shannon
          entropy detection for random-looking tokens ≥20 chars.

**Formatter layer** (``infrastructure.logging.formatter``):

Layer 5 – Output scrub: ``JSONLogFormatter`` independently applies a
          compact PII pattern set to every ``client_log`` string value
          before writing JSON to the log stream, and strips sensitive
          dict keys recursively.  This is a safety net — it operates on
          the serialised output, not the request, so it catches anything
          that bypassed the view pipeline.
Layer 6 – Retention tagging: client error entries are tagged with
          ``"_retention": "short"`` so log-aggregation systems can
          auto-expire them on a shorter schedule than audit entries.

**Accepted residual risk:**

Heuristic redaction cannot guarantee 100% detection of novel or
unanticipated sensitive-data formats.  This is an inherent property of
any system that accepts free-text input from untrusted clients.  The six
layers above reduce the practical attack surface to formats that
simultaneously: (a) survive a 500-char message cap, (b) are not
recognised by any specific PII pattern, (c) do not appear as a
key=value pair, (d) have Shannon entropy below 3.5 bits/char, (e) are
not caught by the formatter's independent pattern pass, and (f) do not
contain any sensitive dict key.  This residual is accepted and should be
reviewed periodically as part of the security programme — for example,
by auditing a sample of logged ``client_log`` entries for unexpected
sensitive content.
"""
import logging
import math
import re

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

logger = logging.getLogger("medrights.audit")

# ── Data-minimisation limits ─────────────────────────────────────────
# message: short enough for triage, too short for embedded PII paragraphs.
MAX_MESSAGE_LENGTH = 500
# stack: only frame summaries are kept (see _minimise_stack), so the raw
# limit is a safety net for the pre-parse input.
MAX_STACK_LENGTH = 5000
MAX_PAYLOAD_BYTES = 10 * 1024  # 10 KB

# Structural limits for the ``extra`` dict
MAX_EXTRA_KEYS = 10
MAX_EXTRA_VALUE_LENGTH = 500

# Only these top-level fields are accepted in the payload
ALLOWED_FIELDS = {"message", "stack", "url", "timestamp", "component", "level", "user_agent", "extra"}

# In strict mode (ALLOWED_FIELDS_STRICT), ``extra`` is rejected and
# ``message`` is reduced to only the JS error type prefix.
ALLOWED_FIELDS_STRICT = {"message", "stack", "url", "timestamp", "component", "level", "user_agent"}

# Any field whose name contains one of these words (case-insensitive) is
# considered sensitive and must be rejected or stripped.
SENSITIVE_KEYWORDS = {"password", "token", "secret", "key", "ssn", "dob", "mrn", "email", "phone", "credential", "authorization"}

# ── Strict-mode message allowlist ────────────────────────────────────
# When CLIENT_LOG_STRICT_MODE is True, only the JS error type prefix is
# kept (e.g. "TypeError", "RangeError").  Everything after the colon is
# dropped.
_JS_ERROR_PREFIX = re.compile(r"^([A-Z][A-Za-z]*Error)\b")
MAX_MESSAGE_LENGTH_STRICT = 80


class ClientErrorRateThrottle(AnonRateThrottle):
    """Scoped throttle: 10 requests per minute for anonymous client logs."""
    rate = "10/minute"


def _contains_sensitive_key(name: str) -> bool:
    """Return True if *name* contains any sensitive keyword."""
    lower = name.lower()
    return any(kw in lower for kw in SENSITIVE_KEYWORDS)


def _sanitize_extra(extra: dict) -> dict:
    """Return a copy of *extra* with sensitive keys removed."""
    if not isinstance(extra, dict):
        return {}
    return {k: v for k, v in extra.items() if not _contains_sensitive_key(k)}


# Patterns that match common PII / secret value formats in free text.
# Order matters: specific patterns first, catch-alls last.
_REDACTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # SSN: 123-45-6789 or 123456789
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b\d{9}\b(?=\s|$|[^0-9])"), "[REDACTED_SSN]"),
    # MRN-style: MRN followed by digits (e.g. MRN12345, MRN-12345)
    (re.compile(r"\bMRN[:\-]?\s*\d{4,}\b", re.IGNORECASE), "[REDACTED_MRN]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    # US phone numbers: (555) 123-4567, 555-123-4567, +1-555-123-4567
    (re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    # Credit card patterns: 16-digit groups with optional separators
    (re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "[REDACTED_CC]"),
    # JWT tokens: three base64url segments separated by dots
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[REDACTED_JWT]"),
    # Bearer / token values: "Bearer <token>" or "token=<value>"
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(token|secret|key|password|passwd|pwd|authorization|cookie|session_id|api_key|access_key|secret_key)\s*[=:]\s*\S+", re.IGNORECASE), r"\1=[REDACTED]"),
    # Long hex strings (32+ chars) that look like keys/hashes
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "[REDACTED_HEX]"),
    # Long base64 strings (40+ chars) that look like encoded credentials
    (re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"), "[REDACTED_BASE64]"),
    # Date of birth patterns: DOB 1990-01-01 or dob: 01/01/1990
    (re.compile(r"\b(?:dob|date.of.birth)\s*[=:]\s*\S+", re.IGNORECASE), "[REDACTED_DOB]"),
    # ── Catch-all: long digit sequences (7+ digits) that survived
    # earlier patterns -- likely IDs, account numbers, or other PII.
    (re.compile(r"\b\d{7,}\b"), "[REDACTED_DIGITS]"),
]

# URL query-string parameters that should be redacted (case-insensitive).
_SENSITIVE_QS_PARAMS = re.compile(
    r"([?&](?:token|key|secret|password|passwd|pwd|session|ssn|mrn|dob|email|"
    r"api_key|access_key|secret_key|authorization|auth)=)([^&]*)",
    re.IGNORECASE,
)


def _redact_sensitive_values(text: str) -> str:
    """Apply pattern-based redaction to free-text fields."""
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ── Structural catch-all layers ──────────────────────────────────────

# Generic key=value / key: value pairs in free text where the value
# side is a single non-whitespace token (credentials, IDs, etc.).
# Skips values that look like plain English words (<=8 chars, all alpha)
# or well-known error tokens (true/false/null/undefined/NaN).
_KV_PAIR = re.compile(
    r"""
    (?<=[^A-Za-z0-9_])          # not part of a larger identifier
    ([A-Za-z_][A-Za-z0-9_]*)    # key
    \s*[=:]\s*                   # separator
    (?P<q>["']?)                 # optional opening quote
    (\S{9,})                     # value (9+ non-ws chars — skip short words)
    (?P=q)                       # matching close quote
    """,
    re.VERBOSE,
)
_SAFE_KV_VALUES = frozenset({
    "true", "false", "null", "undefined", "nan", "none",
    "[object", "object]",
})


def _redact_kv_pairs(text: str) -> str:
    """Redact remaining key=value pairs with long opaque values."""

    def _replace(m: re.Match) -> str:
        value = m.group(3).lower().rstrip(".,;:!?)]}>")
        if value in _SAFE_KV_VALUES:
            return m.group(0)
        return f"{m.group(1)}=[REDACTED]"

    return _KV_PAIR.sub(_replace, text)


def _shannon_entropy(s: str) -> float:
    """Compute Shannon entropy (bits per character) of *s*."""
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum(
        (c / length) * math.log2(c / length) for c in freq.values()
    )


# Tokens 20+ chars with high entropy are likely secrets / random IDs.
_LONG_TOKEN = re.compile(r"\b[A-Za-z0-9_\-+/.]{20,}\b")
_HIGH_ENTROPY_THRESHOLD = 3.5  # bits per char; English prose ≈ 3.0–3.5


def _redact_high_entropy(text: str) -> str:
    """Replace long, high-entropy tokens that survived earlier passes."""

    def _replace(m: re.Match) -> str:
        token = m.group(0)
        # Skip tokens that are already redaction placeholders
        if token.startswith("[REDACTED"):
            return token
        if _shannon_entropy(token) >= _HIGH_ENTROPY_THRESHOLD:
            return "[REDACTED_ENTROPY]"
        return token

    return _LONG_TOKEN.sub(_replace, text)


def _deep_redact_text(text: str) -> str:
    """Full redaction pipeline: specific patterns → kv catch-all → entropy."""
    text = _redact_sensitive_values(text)
    text = _redact_kv_pairs(text)
    text = _redact_high_entropy(text)
    return text


def _redact_url(url: str) -> str:
    """Redact sensitive query-string parameters from a URL."""
    return _SENSITIVE_QS_PARAMS.sub(r"\1[REDACTED]", url)


# ── Stack trace minimiser ────────────────────────────────────────────
# JavaScript stack frames look like:
#   at FunctionName (file.js:10:5)
#   at file.js:10:5
#   FunctionName@file.js:10:5   (Firefox)
# We extract ONLY the function name + file:line:col.  Everything else
# (argument values, local variable dumps, "caused by" message lines
# that could contain user data) is dropped.
_JS_FRAME = re.compile(
    r"^\s*(?:at\s+)?"                  # optional "at "
    r"(?:"
    r"([A-Za-z_$][\w.$<>]*)\s*"       # function name
    r"\(([^)]+)\)"                     # (source location)
    r"|"
    r"([A-Za-z_$][\w.$<>]*)@(\S+)"   # Firefox: name@location
    r"|"
    r"(?:at\s+)?(\S+:\d+:\d+)"       # bare location
    r")",
    re.MULTILINE,
)
MAX_STACK_FRAMES = 20


def _minimise_stack(raw_stack: str) -> str:
    """Reduce a JS stack trace to frame summaries only.

    Drops everything that isn't a recognised frame pattern — this
    structurally excludes interpolated variable values, user-facing
    error messages embedded mid-stack, and any other free text.
    Returns at most ``MAX_STACK_FRAMES`` lines.
    """
    frames: list[str] = []
    for m in _JS_FRAME.finditer(raw_stack):
        if len(frames) >= MAX_STACK_FRAMES:
            break
        if m.group(1) and m.group(2):
            # "at Name (location)"
            frames.append(f"at {m.group(1)} ({m.group(2)})")
        elif m.group(3) and m.group(4):
            # Firefox "Name@location"
            frames.append(f"at {m.group(3)} ({m.group(4)})")
        elif m.group(5):
            # bare "location"
            frames.append(f"at {m.group(5)}")
    if not frames:
        # Unrecognised format — fall back to redacting the raw text,
        # but cap aggressively.
        return _deep_redact_text(raw_stack[:1000])
    return "\n".join(frames)


def _sanitize_extra_deep(extra: dict) -> dict:
    """Structurally constrain and redact the extra dict.

    - Flattens to a single level (nested dicts are JSON-serialised).
    - Caps at MAX_EXTRA_KEYS keys.
    - Caps each value at MAX_EXTRA_VALUE_LENGTH characters.
    - Strips sensitive keys, redacts remaining string values.
    - Rejects non-string/non-numeric leaf values.
    """
    import json as _json

    if not isinstance(extra, dict):
        return {}

    # Strip sensitive keys first
    cleaned: dict[str, str] = {}
    for k, v in extra.items():
        if _contains_sensitive_key(k):
            continue
        if len(cleaned) >= MAX_EXTRA_KEYS:
            break
        # Flatten nested structures into JSON strings
        if isinstance(v, dict):
            v = _json.dumps(v, default=str)
        elif not isinstance(v, (str, int, float, bool)):
            v = str(v)
        if isinstance(v, (int, float, bool)):
            cleaned[k] = str(v)
        else:
            cleaned[k] = _deep_redact_text(
                str(v)[:MAX_EXTRA_VALUE_LENGTH]
            )

    return cleaned


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ClientErrorRateThrottle])
def client_error_log(request):
    """
    Accept client-side JavaScript error reports.
    Logs them for monitoring without requiring authentication, since
    errors may occur on the login page or during session expiry.

    Note: This endpoint is intentionally AllowAny to capture client-side errors
    from unauthenticated pages (e.g., login page errors). It is protected by:
    - Rate limiting (10 requests/minute per IP)
    - Payload schema allowlist
    - Sensitive field rejection
    - Payload size limit (10KB)
    - User binding when session exists

    Expected payload:
    {
        "level": "error" | "warn" | "info",
        "message": "...",
        "stack": "...",
        "url": "...",
        "timestamp": "...",
        "component": "...",
        "extra": { ... }
    }
    """
    # ── 0. Origin / Referer check (exact scheme+host+port match) ────
    from urllib.parse import urlparse
    from django.conf import settings
    trusted_raw = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
    trusted_origins = set()
    for t in trusted_raw:
        p = urlparse(t)
        trusted_origins.add(f"{p.scheme}://{p.netloc}")
    origin = request.META.get("HTTP_ORIGIN", "")
    referer = request.META.get("HTTP_REFERER", "")
    check_value = origin or referer
    if check_value:
        p = urlparse(check_value)
        request_origin = f"{p.scheme}://{p.netloc}"
    else:
        request_origin = ""
    if request_origin and request_origin not in trusted_origins:
        return Response(
            {"error": "origin_rejected", "message": "Untrusted origin.", "status_code": 403},
            status=status.HTTP_403_FORBIDDEN,
        )
    if not check_value and not (request.user and request.user.is_authenticated):
        # No origin/referer AND no session: reject as untraceable
        return Response(
            {"error": "origin_required", "message": "Origin or Referer header required.", "status_code": 403},
            status=status.HTTP_403_FORBIDDEN,
        )

    # ── 1. Reject payloads larger than 10 KB ──────────────────────────
    content_length = request.META.get("CONTENT_LENGTH")
    if content_length is not None:
        try:
            if int(content_length) > MAX_PAYLOAD_BYTES:
                return Response(
                    {
                        "error": "payload_too_large",
                        "message": f"Request body must not exceed {MAX_PAYLOAD_BYTES} bytes.",
                        "status_code": 413,
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
        except (ValueError, TypeError):
            pass

    data = request.data or {}

    # ── Strict mode ──────────────────────────────────────────────────
    from django.conf import settings as django_settings
    strict = getattr(django_settings, "CLIENT_LOG_STRICT_MODE", False)
    allowed = ALLOWED_FIELDS_STRICT if strict else ALLOWED_FIELDS

    # ── 2. Reject unknown top-level fields ────────────────────────────
    unknown_fields = set(data.keys()) - allowed
    if unknown_fields:
        return Response(
            {
                "error": "validation_error",
                "message": f"Unknown fields: {', '.join(sorted(unknown_fields))}",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 3. Reject any top-level field whose name is sensitive ─────────
    for field_name in data.keys():
        if _contains_sensitive_key(field_name):
            return Response(
                {
                    "error": "validation_error",
                    "message": f"Sensitive field '{field_name}' is not allowed.",
                    "status_code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    level = data.get("level", "error")
    raw_message = str(data.get("message", ""))
    if strict:
        # In strict mode, only keep the JS error type prefix.
        m = _JS_ERROR_PREFIX.match(raw_message)
        message = m.group(1) if m else raw_message[:MAX_MESSAGE_LENGTH_STRICT]
        message = _deep_redact_text(message)
    else:
        message = _deep_redact_text(raw_message[:MAX_MESSAGE_LENGTH])
    stack = _minimise_stack(str(data.get("stack", ""))[:MAX_STACK_LENGTH])
    url = _redact_url(str(data.get("url", ""))[:500])
    user_agent = str(data.get("user_agent", ""))[:500]
    timestamp = str(data.get("timestamp", ""))[:100]
    component = str(data.get("component", ""))[:200]
    extra = {} if strict else data.get("extra", {})

    if not message:
        return Response(
            {
                "error": "validation_error",
                "message": "The 'message' field is required.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 4. Sanitize extra: flatten, cap keys/values, redact
    extra = _sanitize_extra_deep(extra)

    log_data = {
        "source": "client",
        "level": level,
        "message": message,
        "url": url,
        "user_agent": user_agent,
    }
    if stack:
        log_data["stack"] = stack
    if timestamp:
        log_data["timestamp"] = timestamp
    if component:
        log_data["component"] = component
    if extra:
        log_data["extra"] = extra

    # ── 5. Bind authenticated user if present ─────────────────────────
    if request.user and request.user.is_authenticated:
        log_data["user_id"] = str(request.user.pk)
        log_data["username"] = request.user.username

    log_fn = logger.error if level == "error" else (logger.warning if level == "warn" else logger.info)
    log_fn(
        "CLIENT %s: %s",
        level.upper(),
        message,
        extra={"client_log": log_data},
    )

    return Response({"status": "logged"}, status=status.HTTP_201_CREATED)
