"""Shared pytest fixtures for MedRights backend tests."""
import base64

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from infrastructure.encryption.service import encryption_service


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def encryption_setup():
    """Initialise the encryption service with a deterministic test key.

    This runs automatically for every test so that any code path touching
    encryption (middleware, serializers, domain helpers) will work without
    extra setup.
    """
    test_key = base64.b64encode(b"test-key-32-bytes-long-xxxxxxxx").decode()
    encryption_service.initialize(test_key)
    yield
    # Reset so each test gets a clean state
    encryption_service._master_key = None


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_user",
        password="AdminPass123!",
        role="admin",
        full_name="Admin User",
        email="admin@example.com",
        is_staff=True,
    )


@pytest.fixture
def frontdesk_user(db):
    return User.objects.create_user(
        username="frontdesk_user",
        password="FrontDesk123!",
        role="front_desk",
        full_name="Front Desk User",
        email="frontdesk@example.com",
    )


@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="clinician_user",
        password="Clinician123!",
        role="clinician",
        full_name="Clinician User",
        email="clinician@example.com",
    )


@pytest.fixture
def compliance_user(db):
    return User.objects.create_user(
        username="compliance_user",
        password="Compliance123!",
        role="compliance",
        full_name="Compliance User",
        email="compliance@example.com",
    )


# ---------------------------------------------------------------------------
# Authenticated API clients
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_client(admin_user):
    """Return an APIClient force-authenticated as the admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    # Ensure a session exists (needed for guest profiles, etc.)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "test-ws-001"
    return client


@pytest.fixture
def frontdesk_client(frontdesk_user):
    client = APIClient()
    client.force_authenticate(user=frontdesk_user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "test-ws-002"
    return client


@pytest.fixture
def clinician_client(clinician_user):
    client = APIClient()
    client.force_authenticate(user=clinician_user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "test-ws-003"
    return client


@pytest.fixture
def compliance_client(compliance_user):
    client = APIClient()
    client.force_authenticate(user=compliance_user)
    client.defaults["HTTP_X_WORKSTATION_ID"] = "test-ws-004"
    return client


# ---------------------------------------------------------------------------
# Sample patient (created via API)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_patient(auth_client):
    """Create a patient via the API and return the response data."""
    payload = {
        "mrn": "MRN-001",
        "ssn": "123456789",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "gender": "Male",
        "phone": "5551234567",
        "email": "john.doe@example.com",
        "address": "123 Main St, Anytown, USA",
    }
    response = auth_client.post("/api/v1/patients/create/", payload, format="json")
    assert response.status_code == 201, f"Patient creation failed: {response.data}"
    return response.data
