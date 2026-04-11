"""Custom DRF permissions for the MedRights portal."""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only users with the 'admin' role may access."""

    message = "Administrator privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsComplianceOfficer(BasePermission):
    """Only users with the 'compliance' role may access."""

    message = "Compliance officer privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "compliance"
        )


class IsFrontDeskOrAdmin(BasePermission):
    """Users with 'front_desk' or 'admin' role may access."""

    message = "Front-desk or administrator privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("front_desk", "admin")
        )


class IsFrontDeskOrClinicianOrAdmin(BasePermission):
    """Users with 'front_desk', 'clinician', or 'admin' role may access."""

    message = "Front-desk, clinician, or administrator privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("front_desk", "clinician", "admin")
        )


class IsComplianceOrAdmin(BasePermission):
    """Users with 'compliance' or 'admin' role may access."""

    message = "Compliance officer or administrator privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("compliance", "admin")
        )


class SudoRequired(BasePermission):
    """
    Requires an active sudo token for a specific action class.
    The view must set ``view.sudo_action_class`` to indicate
    which action class is required.

    The SudoModeMiddleware populates ``request.sudo_actions`` with the
    set of active (non-expired) action classes for the current session.
    """

    message = "Sudo mode required. Please re-authenticate to perform this action."

    def has_permission(self, request, view):
        required_action = getattr(view, "sudo_action_class", None)
        if required_action is None:
            return False
        return required_action in getattr(request, "sudo_actions", set())
