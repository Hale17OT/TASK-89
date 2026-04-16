"""Shared fixtures and helpers for black-box HTTP API tests.

All tests in this package use Django's test Client with session-based
login — NOT force_authenticate — so the full middleware stack is exercised.
"""
import io
import json
import uuid

import pytest
from django.test import Client
from PIL import Image

from apps.accounts.models import User

WS = {"HTTP_X_WORKSTATION_ID": "ws-bb"}
BB_PASSWORD = "Pass1234!"


# ---------------------------------------------------------------------------
# User fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def bb_users(db):
    users = {}
    for uname, role, pwd in [
        ("bb_admin", "admin", BB_PASSWORD),
        ("bb_fd", "front_desk", BB_PASSWORD),
        ("bb_clin", "clinician", BB_PASSWORD),
        ("bb_comp", "compliance", BB_PASSWORD),
    ]:
        users[role] = User.objects.create_user(username=uname, password=pwd, role=role)
    return users


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------

def make_client(username, password=BB_PASSWORD):
    c = Client()
    c.login(username=username, password=password)
    return c


def admin():
    return make_client("bb_admin")


def frontdesk():
    return make_client("bb_fd")


def clinician():
    return make_client("bb_clin")


def compliance():
    return make_client("bb_comp")


def anon():
    return Client()


def admin_with_sudo(action_class):
    """Login as admin and acquire a sudo token."""
    c = admin()
    c.post(
        "/api/v1/sudo/acquire/",
        json.dumps({"password": BB_PASSWORD, "action_class": action_class}),
        content_type="application/json",
        **WS,
    )
    return c


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def test_image():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, "PNG")
    buf.seek(0)
    buf.name = "test.png"
    return buf


def create_patient(client_fn=None):
    c = client_fn() if client_fn else admin()
    r = c.post(
        "/api/v1/patients/create/",
        json.dumps({
            "mrn": f"MRN-{uuid.uuid4().hex[:6]}",
            "ssn": "123456789",
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": "1985-06-15",
            "gender": "Female",
            "phone": "5559876543",
            "email": "jane@example.com",
            "address": "456 Oak Ave",
        }),
        content_type="application/json",
        **WS,
    )
    assert r.status_code == 201, f"Patient creation failed: {r.content}"
    return r.json()


def upload_media(client_fn=None):
    c = client_fn() if client_fn else admin()
    img = test_image()
    r = c.post("/api/v1/media/upload/", {"file": img}, **WS)
    assert r.status_code == 201
    return r.json()


def create_order(client_fn=None, patient_id=None):
    c = client_fn() if client_fn else admin()
    if not patient_id:
        p = create_patient()
        patient_id = p["id"]
    r = c.post(
        "/api/v1/financials/orders/",
        json.dumps({
            "patient_id": patient_id,
            "line_items": [
                {"description": "Consultation", "quantity": 1, "unit_price": "150.00"},
            ],
            "notes": "Test order",
        }),
        content_type="application/json",
        **WS,
    )
    assert r.status_code == 201, f"Order creation failed: {r.content}"
    return r.json()


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def assert_denied(r):
    """Assert a 401/403 response has a well-formed error body."""
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"
    body = r.json()
    assert "detail" in body or "error" in body, f"Denial response missing 'error' or 'detail': {body}"


def assert_role_denied(r, expected_status=403):
    """Assert a role-based 403 with error schema."""
    assert r.status_code == expected_status
    body = r.json()
    assert "detail" in body or "error" in body, f"403 response missing error schema: {body}"
