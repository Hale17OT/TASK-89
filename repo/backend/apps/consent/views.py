"""Consent views: CRUD and revocation for patient consent records."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsFrontDeskOrClinicianOrAdmin
from apps.mpi.models import Patient

from .models import Consent
from .serializers import (
    ConsentCreateSerializer,
    ConsentListSerializer,
    ConsentRevokeSerializer,
)

logger = logging.getLogger("medrights.consent")


def _get_patient_or_404(patient_id):
    """Retrieve a patient or return a 404-style tuple."""
    try:
        return Patient.objects.get(pk=patient_id), None
    except Patient.DoesNotExist:
        return None, Response(
            {
                "error": "not_found",
                "message": "Patient not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )


# ── List + Create ──────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def consent_list_create(request, patient_id):
    """
    GET  /api/v1/patients/{pid}/consents/  -- list consents
    POST /api/v1/patients/{pid}/consents/  -- create consent
    """
    patient, err = _get_patient_or_404(patient_id)
    if err:
        return err

    if request.method == "GET":
        consents = Consent.objects.filter(patient=patient).select_related(
            "granted_by", "revoked_by",
        ).prefetch_related("scopes")

        serializer = ConsentListSerializer(consents, many=True)

        request._audit_context = {
            "event_type": "consent_list",
            "target_model": "Patient",
            "target_id": str(patient.id),
            "target_repr": f"Consents for patient {patient.mrn_search_hash[:8]}...",
        }

        return Response({"results": serializer.data, "count": consents.count()})

    # POST -- create consent (role already enforced by IsFrontDeskOrClinicianOrAdmin)
    return _consent_create(request, patient)


def _consent_create(request, patient):
    """Internal: create a consent for an already-resolved patient."""
    serializer = ConsentCreateSerializer(
        data=request.data,
        context={"request": request, "patient": patient},
    )
    serializer.is_valid(raise_exception=True)
    consent = serializer.save()

    request._audit_context = {
        "event_type": "consent_create",
        "target_model": "Consent",
        "target_id": str(consent.id),
        "target_repr": f"Consent '{consent.purpose}' for patient {patient.id}",
    }

    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── Detail ──────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def consent_detail(request, patient_id, pk):
    """
    GET /api/v1/patients/{pid}/consents/{id}/

    Retrieve a single consent record.
    """
    patient, err = _get_patient_or_404(patient_id)
    if err:
        return err

    try:
        consent = Consent.objects.select_related(
            "granted_by", "revoked_by",
        ).prefetch_related("scopes").get(pk=pk, patient=patient)
    except Consent.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Consent not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ConsentListSerializer(consent)

    request._audit_context = {
        "event_type": "consent_view",
        "target_model": "Consent",
        "target_id": str(consent.id),
        "target_repr": f"Consent '{consent.purpose}' for patient {patient.id}",
    }

    return Response(serializer.data)


# ── Revoke ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def consent_revoke(request, patient_id, pk):
    """
    POST /api/v1/patients/{pid}/consents/{id}/revoke/

    Revoke an active consent.  If a physical copy is on file the
    caller must explicitly acknowledge the warning.
    """
    patient, err = _get_patient_or_404(patient_id)
    if err:
        return err

    try:
        consent = Consent.objects.get(pk=pk, patient=patient)
    except Consent.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Consent not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ConsentRevokeSerializer(
        data=request.data,
        context={"request": request, "consent": consent},
    )
    serializer.is_valid(raise_exception=True)
    revoked_consent = serializer.save()

    request._audit_context = {
        "event_type": "consent_revoke",
        "target_model": "Consent",
        "target_id": str(revoked_consent.id),
        "target_repr": f"Consent '{revoked_consent.purpose}' for patient {patient.id}",
        "extra_data": {
            "revocation_reason": revoked_consent.revocation_reason,
        },
    }

    result = ConsentListSerializer(revoked_consent).data
    return Response(result)
