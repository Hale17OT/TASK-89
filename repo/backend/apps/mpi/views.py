"""MPI views: patient CRUD, search, and break-glass access."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsFrontDeskOrAdmin, IsFrontDeskOrClinicianOrAdmin
from domain.services.patient_service import compute_patient_search_hash

from .models import BreakGlassLog, Patient
from .serializers import (
    BreakGlassSerializer,
    PatientCreateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
    PatientUpdateSerializer,
    models_q_mrn_or_ssn,
)

logger = logging.getLogger("medrights.mpi")


# ── Search ──────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def patient_search(request):
    """
    GET /api/v1/patients/?q=<search_term>

    Search patients by MRN or SSN using HMAC comparison.
    The search term is never logged in plaintext.
    """
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response(
            {
                "error": "missing_query",
                "message": "The 'q' query parameter is required.",
                "status_code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    search_hash = compute_patient_search_hash(query)
    patients = Patient.objects.filter(
        models_q_mrn_or_ssn(search_hash),
        is_active=True,
    )

    serializer = PatientListSerializer(patients, many=True)

    request._audit_context = {
        "event_type": "mpi_patient_search",
        "target_model": "Patient",
        "target_repr": f"search (hash={search_hash[:8]}...)",
        "extra_data": {"result_count": patients.count()},
    }

    return Response(serializer.data)


# ── Create ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsFrontDeskOrAdmin])
def patient_create(request):
    """
    POST /api/v1/patients/

    Create a new patient record with encrypted PII.
    """
    serializer = PatientCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    patient = serializer.save()

    request._audit_context = {
        "event_type": "mpi_patient_create",
        "target_model": "Patient",
        "target_id": str(patient.id),
        "target_repr": f"Patient {patient.mrn_search_hash[:8]}...",
    }

    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── Detail ──────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def patient_detail(request, pk):
    """
    GET /api/v1/patients/{id}/

    Return masked patient detail.  If an active break-glass session
    exists for this user+patient combo, return unmasked.
    """
    try:
        patient = Patient.objects.get(pk=pk)
    except Patient.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Patient not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check for active break-glass (within the last 15 minutes)
    from django.utils import timezone
    import datetime

    break_glass_active = BreakGlassLog.objects.filter(
        user=request.user,
        patient=patient,
        accessed_at__gte=timezone.now() - datetime.timedelta(minutes=15),
    ).exists()

    serializer = PatientDetailSerializer(
        patient,
        context={
            "request": request,
            "break_glass_active": break_glass_active,
        },
    )

    request._audit_context = {
        "event_type": "mpi_patient_view",
        "target_model": "Patient",
        "target_id": str(patient.id),
        "target_repr": f"Patient {patient.mrn_search_hash[:8]}...",
        "extra_data": {"break_glass_active": break_glass_active},
    }

    return Response(serializer.data)


# ── Update ──────────────────────────────────────────────────────────

@api_view(["PATCH"])
@permission_classes([IsFrontDeskOrAdmin])
def patient_update(request, pk):
    """
    PATCH /api/v1/patients/{id}/

    Update patient fields.  Changed PII is re-encrypted and search
    hashes are recomputed.
    """
    try:
        patient = Patient.objects.get(pk=pk)
    except Patient.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Patient not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = PatientUpdateSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    updated_patient, changed_fields = serializer.update(patient, serializer.validated_data)

    request._audit_context = {
        "event_type": "mpi_patient_update",
        "target_model": "Patient",
        "target_id": str(updated_patient.id),
        "target_repr": f"Patient {updated_patient.mrn_search_hash[:8]}...",
        "field_changes": {f: {"changed": True} for f in changed_fields},
    }

    detail_serializer = PatientDetailSerializer(
        updated_patient,
        context={"request": request, "break_glass_active": False},
    )
    return Response(detail_serializer.data)


# ── Break Glass ─────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsFrontDeskOrClinicianOrAdmin])
def break_glass(request, pk):
    """
    POST /api/v1/patients/{id}/break-glass/

    Create a break-glass log and return unmasked patient data.
    """
    try:
        patient = Patient.objects.get(pk=pk)
    except Patient.DoesNotExist:
        return Response(
            {
                "error": "not_found",
                "message": "Patient not found.",
                "status_code": 404,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = BreakGlassSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    client_ip = getattr(request, "client_ip", request.META.get("REMOTE_ADDR", "0.0.0.0"))
    workstation_id = getattr(request, "workstation_id", request.headers.get("X-Workstation-ID", ""))

    # All PII fields that will be unmasked
    fields_accessed = [
        "mrn", "ssn", "first_name", "last_name",
        "date_of_birth", "phone", "email", "address",
    ]

    log_entry = BreakGlassLog.objects.create(
        user=request.user,
        patient=patient,
        justification=serializer.validated_data["justification"],
        justification_category=serializer.validated_data["justification_category"],
        fields_accessed=fields_accessed,
        ip_address=client_ip,
        workstation_id=workstation_id,
    )

    logger.warning(
        "Break-glass access: user=%s patient=%s category=%s",
        request.user.id,
        patient.id,
        serializer.validated_data["justification_category"],
    )

    request._audit_context = {
        "event_type": "mpi_break_glass",
        "target_model": "Patient",
        "target_id": str(patient.id),
        "target_repr": f"Patient {patient.mrn_search_hash[:8]}...",
        "extra_data": {
            "break_glass_log_id": str(log_entry.id),
            "justification_category": log_entry.justification_category,
            "fields_accessed": fields_accessed,
        },
    }

    # Return unmasked patient data
    detail_serializer = PatientDetailSerializer(
        patient,
        context={
            "request": request,
            "break_glass_active": True,
        },
    )

    return Response(
        {
            "break_glass_log_id": str(log_entry.id),
            "patient": detail_serializer.data,
        },
        status=status.HTTP_201_CREATED,
    )
