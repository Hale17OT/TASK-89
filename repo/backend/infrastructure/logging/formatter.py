"""JSON log formatter for structured logging.

This formatter is the **last line of defence** before data reaches the
log stream.  For ``client_log`` records (originating from the public
client-error endpoint), it applies an independent PII scrub pass and
tags them with ``"_retention": "short"`` for accelerated expiry.  See
``apps.audit.views_client_logs`` for the full defence-in-depth model.
"""
import json
import logging
import re
import traceback
from datetime import datetime, timezone

# Standard LogRecord attributes -- excluded from the extras dict.
_BUILTIN_ATTRS = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs", "msg",
    "name", "pathname", "process", "processName", "relativeCreated",
    "stack_info", "taskName", "thread", "threadName",
})

_SENSITIVE_KEYWORDS = frozenset({
    "password", "token", "secret", "key", "ssn", "dob", "mrn",
    "authorization", "credential", "email", "phone",
})

# ── Formatter-level PII scrubbing (defence-in-depth) ─────────────────
# These patterns run on every string value that reaches the JSON output,
# acting as a safety net if upstream sanitisation misses something.
_SCRUB_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SCRUBBED]"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[SCRUBBED]"),
    (re.compile(r"\bMRN[:\-]?\s*\d{4,}\b", re.IGNORECASE), "[SCRUBBED]"),
    (re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[SCRUBBED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[SCRUBBED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [SCRUBBED]"),
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "[SCRUBBED]"),
]


def _is_sensitive(name: str) -> bool:
    lower = name.lower()
    return any(s in lower for s in _SENSITIVE_KEYWORDS)


def _scrub_string(value: str) -> str:
    """Last-resort PII scrub applied at the formatter output layer."""
    for pattern, replacement in _SCRUB_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def _scrub_value(value):
    """Recursively scrub string values in dicts, lists, or bare strings."""
    if isinstance(value, str):
        return _scrub_string(value)
    if isinstance(value, dict):
        return {
            k: _scrub_value(v) for k, v in value.items()
            if not _is_sensitive(k)
        }
    if isinstance(value, (list, tuple)):
        return [_scrub_value(item) for item in value]
    return value


class JSONLogFormatter(logging.Formatter):
    """Formats log records as JSON for Docker stdout consumption.

    Extracts *all* non-builtin attributes from the LogRecord (these are
    the fields passed via ``extra={...}`` on log calls) and includes
    them in the JSON output after scrubbing sensitive keys.

    A formatter-level PII scrub pass runs on all ``client_log`` string
    values as a defence-in-depth measure — even if the view-layer
    sanitisation misses a sensitive value, the formatter catches known
    PII patterns before they reach the log stream.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Walk every attribute on the record; anything that is NOT a
        # standard builtin is an application-supplied extra.
        extras: dict = {}
        for attr, value in record.__dict__.items():
            if attr.startswith("_") or attr in _BUILTIN_ATTRS:
                continue
            if _is_sensitive(attr):
                continue
            # Promote well-known context keys to top level
            if attr in ("request_id", "user_id", "username", "category"):
                log_entry[attr] = value
            elif attr == "client_log" and isinstance(value, dict):
                # Defence-in-depth: scrub every value in client_log
                # at the output layer, independent of view sanitisation.
                log_entry["client_log"] = _scrub_value(value)
                log_entry["_retention"] = "short"
            else:
                extras[attr] = value

        if extras:
            log_entry["extra"] = extras

        # Exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str)
