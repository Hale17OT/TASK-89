"""Integration tests for the Patient / MPI API endpoints."""
import pytest

from apps.mpi.models import Patient


pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Create
# ------------------------------------------------------------------

class TestPatientCreate:
    def test_create_patient(self, auth_client):
        resp = auth_client.post(
            "/api/v1/patients/create/",
            {
                "mrn": "MRN-100",
                "ssn": "111223333",
                "first_name": "Alice",
                "last_name": "Smith",
                "date_of_birth": "1985-06-15",
                "gender": "Female",
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.data
        assert "id" in data
        # Response should be masked
        assert data["mrn"] != "MRN-100"  # masked
        assert "A" in data["name"]  # first letter of "Alice" visible


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------

class TestPatientSearch:
    def test_search_patient_by_mrn(self, auth_client, sample_patient):
        resp = auth_client.get("/api/v1/patients/", {"q": "MRN-001"})
        assert resp.status_code == 200
        results = resp.data
        assert len(results) >= 1
        # The returned ID should match the created patient
        ids = [r["id"] for r in results]
        assert sample_patient["id"] in ids

    def test_search_no_results(self, auth_client, sample_patient):
        resp = auth_client.get("/api/v1/patients/", {"q": "NONEXISTENT-999"})
        assert resp.status_code == 200
        assert resp.data == []

    def test_search_requires_query(self, auth_client):
        resp = auth_client.get("/api/v1/patients/")
        assert resp.status_code == 400
        assert resp.data["error"] == "missing_query"


# ------------------------------------------------------------------
# Detail (masked)
# ------------------------------------------------------------------

class TestPatientDetail:
    def test_patient_detail_masked(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        resp = auth_client.get(f"/api/v1/patients/{pid}/")
        assert resp.status_code == 200
        data = resp.data
        # SSN should be masked: ***-**-6789
        assert data["ssn"].startswith("***")
        # First name should be masked: J***
        assert data["first_name"][0] == "J"
        assert "*" in data["first_name"]


# ------------------------------------------------------------------
# Break glass
# ------------------------------------------------------------------

class TestBreakGlass:
    def test_break_glass_unmasks(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        resp = auth_client.post(
            f"/api/v1/patients/{pid}/break-glass/",
            {
                "justification": "Emergency treatment required for this patient immediately",
                "justification_category": "emergency",
            },
            format="json",
        )
        assert resp.status_code == 201
        patient_data = resp.data["patient"]
        # After break-glass, data should be unmasked
        assert patient_data["first_name"] == "John"
        assert patient_data["last_name"] == "Doe"
        assert patient_data["ssn"] == "123456789"

    def test_break_glass_short_justification(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        resp = auth_client.post(
            f"/api/v1/patients/{pid}/break-glass/",
            {
                "justification": "too short",
                "justification_category": "emergency",
            },
            format="json",
        )
        # BreakGlassSerializer requires min_length=20 on justification
        assert resp.status_code == 400


# ------------------------------------------------------------------
# Update
# ------------------------------------------------------------------

class TestPatientUpdate:
    def test_patient_update(self, auth_client, sample_patient):
        pid = sample_patient["id"]
        resp = auth_client.patch(
            f"/api/v1/patients/{pid}/update/",
            {"first_name": "Jane", "gender": "Female"},
            format="json",
        )
        assert resp.status_code == 200
        # The response is masked, so verify through break-glass
        bg = auth_client.post(
            f"/api/v1/patients/{pid}/break-glass/",
            {
                "justification": "Verifying update was applied correctly to the record",
                "justification_category": "admin",
            },
            format="json",
        )
        assert bg.status_code == 201
        assert bg.data["patient"]["first_name"] == "Jane"
        assert bg.data["patient"]["gender"] == "Female"
