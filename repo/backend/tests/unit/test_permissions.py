"""Unit tests for custom DRF permission classes."""
import pytest
from types import SimpleNamespace

from apps.accounts.permissions import (
    IsAdmin,
    IsComplianceOfficer,
    IsComplianceOrAdmin,
    IsFrontDeskOrAdmin,
    IsFrontDeskOrClinicianOrAdmin,
    SudoRequired,
)


def _user(role, authenticated=True):
    return SimpleNamespace(
        is_authenticated=authenticated,
        role=role,
    )


def _request(user=None):
    return SimpleNamespace(user=user or SimpleNamespace(is_authenticated=False))


def _view(**attrs):
    return SimpleNamespace(**attrs)


# ---------------------------------------------------------------------------
# IsAdmin
# ---------------------------------------------------------------------------

class TestIsAdmin:
    perm = IsAdmin()

    def test_admin_allowed(self):
        assert self.perm.has_permission(_request(_user("admin")), _view()) is True

    def test_front_desk_denied(self):
        assert self.perm.has_permission(_request(_user("front_desk")), _view()) is False

    def test_clinician_denied(self):
        assert self.perm.has_permission(_request(_user("clinician")), _view()) is False

    def test_compliance_denied(self):
        assert self.perm.has_permission(_request(_user("compliance")), _view()) is False

    def test_unauthenticated_denied(self):
        assert self.perm.has_permission(_request(_user("admin", authenticated=False)), _view()) is False

    def test_no_user_denied(self):
        req = SimpleNamespace(user=None)
        assert not self.perm.has_permission(req, _view())


# ---------------------------------------------------------------------------
# IsComplianceOfficer
# ---------------------------------------------------------------------------

class TestIsComplianceOfficer:
    perm = IsComplianceOfficer()

    def test_compliance_allowed(self):
        assert self.perm.has_permission(_request(_user("compliance")), _view()) is True

    def test_admin_denied(self):
        assert self.perm.has_permission(_request(_user("admin")), _view()) is False

    def test_front_desk_denied(self):
        assert self.perm.has_permission(_request(_user("front_desk")), _view()) is False

    def test_clinician_denied(self):
        assert self.perm.has_permission(_request(_user("clinician")), _view()) is False

    def test_unauthenticated_denied(self):
        assert self.perm.has_permission(_request(_user("compliance", authenticated=False)), _view()) is False


# ---------------------------------------------------------------------------
# IsFrontDeskOrAdmin
# ---------------------------------------------------------------------------

class TestIsFrontDeskOrAdmin:
    perm = IsFrontDeskOrAdmin()

    def test_admin_allowed(self):
        assert self.perm.has_permission(_request(_user("admin")), _view()) is True

    def test_front_desk_allowed(self):
        assert self.perm.has_permission(_request(_user("front_desk")), _view()) is True

    def test_clinician_denied(self):
        assert self.perm.has_permission(_request(_user("clinician")), _view()) is False

    def test_compliance_denied(self):
        assert self.perm.has_permission(_request(_user("compliance")), _view()) is False

    def test_unauthenticated_denied(self):
        assert self.perm.has_permission(_request(_user("admin", authenticated=False)), _view()) is False


# ---------------------------------------------------------------------------
# IsFrontDeskOrClinicianOrAdmin
# ---------------------------------------------------------------------------

class TestIsFrontDeskOrClinicianOrAdmin:
    perm = IsFrontDeskOrClinicianOrAdmin()

    def test_admin_allowed(self):
        assert self.perm.has_permission(_request(_user("admin")), _view()) is True

    def test_front_desk_allowed(self):
        assert self.perm.has_permission(_request(_user("front_desk")), _view()) is True

    def test_clinician_allowed(self):
        assert self.perm.has_permission(_request(_user("clinician")), _view()) is True

    def test_compliance_denied(self):
        assert self.perm.has_permission(_request(_user("compliance")), _view()) is False

    def test_unauthenticated_denied(self):
        assert self.perm.has_permission(_request(_user("clinician", authenticated=False)), _view()) is False


# ---------------------------------------------------------------------------
# IsComplianceOrAdmin
# ---------------------------------------------------------------------------

class TestIsComplianceOrAdmin:
    perm = IsComplianceOrAdmin()

    def test_admin_allowed(self):
        assert self.perm.has_permission(_request(_user("admin")), _view()) is True

    def test_compliance_allowed(self):
        assert self.perm.has_permission(_request(_user("compliance")), _view()) is True

    def test_front_desk_denied(self):
        assert self.perm.has_permission(_request(_user("front_desk")), _view()) is False

    def test_clinician_denied(self):
        assert self.perm.has_permission(_request(_user("clinician")), _view()) is False

    def test_unauthenticated_denied(self):
        assert self.perm.has_permission(_request(_user("admin", authenticated=False)), _view()) is False


# ---------------------------------------------------------------------------
# SudoRequired
# ---------------------------------------------------------------------------

class TestSudoRequired:
    perm = SudoRequired()

    def test_allowed_when_action_class_in_sudo_actions(self):
        req = SimpleNamespace(sudo_actions={"user_disable", "bulk_export"})
        view = _view(sudo_action_class="user_disable")
        assert self.perm.has_permission(req, view) is True

    def test_denied_when_action_class_not_in_sudo_actions(self):
        req = SimpleNamespace(sudo_actions={"bulk_export"})
        view = _view(sudo_action_class="user_disable")
        assert self.perm.has_permission(req, view) is False

    def test_denied_when_sudo_actions_empty(self):
        req = SimpleNamespace(sudo_actions=set())
        view = _view(sudo_action_class="user_disable")
        assert self.perm.has_permission(req, view) is False

    def test_denied_when_no_sudo_actions_attr(self):
        req = SimpleNamespace()
        view = _view(sudo_action_class="user_disable")
        assert self.perm.has_permission(req, view) is False

    def test_denied_when_view_has_no_sudo_action_class(self):
        req = SimpleNamespace(sudo_actions={"user_disable"})
        view = _view()  # no sudo_action_class
        assert self.perm.has_permission(req, view) is False
