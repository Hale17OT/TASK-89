"""
Pure-Python patient domain service.
No Django imports -- only stdlib + infrastructure encryption.
"""
import re

from domain.exceptions import ValidationError
from infrastructure.encryption.service import encryption_service


# ── Field validation rules ──────────────────────────────────────────
REQUIRED_FIELDS = ("mrn", "first_name", "last_name", "date_of_birth")

MRN_PATTERN = re.compile(r"^[A-Za-z0-9\-]{1,20}$")
SSN_PATTERN = re.compile(r"^\d{3}-?\d{2}-?\d{4}$")


def validate_patient_data(data: dict) -> list[str]:
    """
    Validate patient data and return a list of error messages.
    Returns an empty list when everything is valid.
    """
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            errors.append(f"{field} is required.")

    mrn = data.get("mrn", "")
    if mrn and not MRN_PATTERN.match(mrn):
        errors.append("MRN must be 1-20 alphanumeric characters or hyphens.")

    ssn = data.get("ssn", "")
    if ssn and not SSN_PATTERN.match(ssn):
        errors.append("SSN must be in the format 123-45-6789 or 123456789.")

    if errors:
        raise ValidationError(errors)

    return errors


# ── HMAC search hash ────────────────────────────────────────────────

def compute_patient_search_hash(value: str) -> str:
    """Compute an HMAC-SHA256 search hash for a patient field value."""
    if not value:
        return ""
    # Normalise: strip whitespace, lowercase
    normalised = value.strip().lower()
    return encryption_service.compute_hmac(normalised, purpose="patient_search")


# ── Masking helpers ─────────────────────────────────────────────────

def mask_patient_field(value: str, field_type: str) -> str:
    """
    Mask a PII field value for display.

    Supported field_type values:
        ssn   -> ***-**-1234
        name  -> J***
        dob   -> **/**/1990  (expects YYYY-MM-DD or MM/DD/YYYY)
        phone -> (***) ***-1234
        email -> j****@***.com
        default -> last-4 visible
    """
    if not value:
        return "****"

    if field_type == "ssn":
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 4:
            return f"***-**-{digits[-4:]}"
        return "***-**-****"

    if field_type == "name":
        if len(value) <= 1:
            return "*"
        return value[0] + "*" * (len(value) - 1)

    if field_type == "dob":
        # Accepts YYYY-MM-DD or similar; always shows only year
        parts = re.split(r"[-/]", value)
        if len(parts) == 3:
            # YYYY-MM-DD
            if len(parts[0]) == 4:
                return f"**/**/{ parts[0]}"
            # MM/DD/YYYY
            return f"**/**/{parts[2]}"
        return "**/**/****"

    if field_type == "phone":
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 4:
            return f"(***) ***-{digits[-4:]}"
        return "(***) ***-****"

    if field_type == "email":
        if "@" in value:
            local, domain = value.rsplit("@", 1)
            masked_local = local[0] + "*" * (len(local) - 1) if local else "****"
            domain_parts = domain.split(".")
            masked_domain = ".".join(
                "*" * len(p) if i < len(domain_parts) - 1 else p
                for i, p in enumerate(domain_parts)
            )
            return f"{masked_local}@{masked_domain}"
        return "*" * max(len(value) - 4, 0) + value[-4:]

    # default
    return encryption_service.mask_value(value, mask_type="default")
