"""
Pure-Python consent domain service.
No Django ORM imports -- works with plain values / dicts.
"""
from datetime import date, datetime

from domain.exceptions import ConflictError, ValidationError


def compute_consent_status(
    *,
    is_revoked: bool,
    revoked_at: datetime | None = None,
    expiration_date: date | None = None,
    effective_date: date | None = None,
) -> str:
    """
    Determine the current status of a consent record.

    Returns one of: "active", "expired", "revoked".
    """
    if is_revoked:
        return "revoked"

    today = date.today()

    if expiration_date and expiration_date < today:
        return "expired"

    if effective_date and effective_date > today:
        # Not yet effective -- still considered "active" (pending start)
        return "active"

    return "active"


def validate_consent_dates(
    effective_date: date,
    expiration_date: date | None,
) -> None:
    """
    Validate that the expiration date (if provided) is after the
    effective date.

    Raises domain.exceptions.ValidationError on failure.
    """
    if expiration_date is not None and expiration_date <= effective_date:
        raise ValidationError(
            "Expiration date must be after the effective date."
        )


def validate_revocation(
    *,
    is_revoked: bool,
    physical_copy_on_file: bool,
    acknowledged_warning: bool,
) -> None:
    """
    Validate that a consent can be revoked.

    Raises ConflictError if already revoked.
    Raises ValidationError if a physical-copy warning acknowledgement is
    required but was not provided.
    """
    if is_revoked:
        raise ConflictError("This consent has already been revoked.")

    if physical_copy_on_file and not acknowledged_warning:
        raise ValidationError(
            "A physical copy of this consent is on file. "
            "You must acknowledge the physical_copy_warning before revoking."
        )


def validate_consent_for_media(
    *,
    is_revoked: bool,
    expiration_date: date | None = None,
    effective_date: date | None = None,
    scope_types: list[str],
    media_use_scope_values: list[str],
    required_media_use: str = "capture_storage",
    consent_patient_id: str | None = None,
    target_patient_id: str | None = None,
) -> None:
    """
    Validate that a consent record authorises media use.

    Checks:
    1. Consent is not revoked.
    2. Consent is not expired (expiration_date >= today).
    3. Consent effective_date has been reached (<= today).
    4. Consent includes at least one ``media_use`` scope_type.
    5. At least one ``media_use`` scope value must match
       *required_media_use* (defaults to ``"capture_storage"``).
    6. If both patient IDs are given, they must match.

    Parameters
    ----------
    scope_types :
        All scope_type values attached to the consent.  An empty list
        means the consent has no scopes and will be rejected.
    media_use_scope_values :
        The scope_value strings for scopes whose scope_type is
        ``media_use``.
    required_media_use :
        The specific media-use scope value required for the operation.
        Defaults to ``"capture_storage"``.

    Raises ``ValidationError`` on any check failure.
    """
    if is_revoked:
        raise ValidationError(
            "Cannot use media under a revoked consent."
        )

    today = date.today()

    if expiration_date is not None and expiration_date < today:
        raise ValidationError(
            "Cannot use media under an expired consent."
        )

    if effective_date is not None and effective_date > today:
        raise ValidationError(
            "Consent is not yet effective."
        )

    if "media_use" not in scope_types:
        raise ValidationError(
            "Consent does not include a 'media_use' scope."
        )

    if required_media_use not in media_use_scope_values:
        raise ValidationError(
            f"Consent 'media_use' scope does not cover "
            f"'{required_media_use}'."
        )

    if (
        consent_patient_id is not None
        and target_patient_id is not None
        and str(consent_patient_id) != str(target_patient_id)
    ):
        raise ValidationError(
            "Consent does not belong to the target patient."
        )
