"""MPI serializers: handle encryption, masking, and break-glass logic."""
import logging

from rest_framework import serializers

from domain.services.patient_service import (
    compute_patient_search_hash,
    mask_patient_field,
)
from infrastructure.encryption.service import encryption_service

from .models import BreakGlassLog, Patient

logger = logging.getLogger("medrights.mpi")

ENCRYPT_PURPOSE = "patient_pii"


# ── helpers ─────────────────────────────────────────────────────────

def _encrypt(value: str) -> bytes:
    """Encrypt a plaintext string for patient PII storage."""
    return encryption_service.encrypt_aes_gcm(value, purpose=ENCRYPT_PURPOSE)


def _decrypt(data: bytes) -> str:
    """Decrypt patient PII ciphertext back to plaintext."""
    if not data:
        return ""
    return encryption_service.decrypt_aes_gcm(bytes(data), purpose=ENCRYPT_PURPOSE)


def _masked_name(patient: Patient) -> str:
    """Return masked 'F*** L**' representation."""
    first = _decrypt(patient.first_name_encrypted)
    last = _decrypt(patient.last_name_encrypted)
    return f"{mask_patient_field(first, 'name')} {mask_patient_field(last, 'name')}"


# ── PatientCreateSerializer ─────────────────────────────────────────

class PatientCreateSerializer(serializers.Serializer):
    """
    Accepts plaintext PII, encrypts everything, stores ciphertext.
    """

    mrn = serializers.CharField(max_length=20)
    ssn = serializers.CharField(max_length=11, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateField()
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_mrn(self, value):
        mrn_hash = compute_patient_search_hash(value)
        if Patient.objects.filter(mrn_search_hash=mrn_hash).exists():
            raise serializers.ValidationError("A patient with this MRN already exists.")
        return value

    def create(self, validated_data):
        mrn = validated_data["mrn"]
        ssn = validated_data.get("ssn", "")
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]
        dob = str(validated_data["date_of_birth"])
        gender = validated_data.get("gender", "")
        phone = validated_data.get("phone", "")
        email = validated_data.get("email", "")
        address = validated_data.get("address", "")

        patient = Patient.objects.create(
            mrn_encrypted=_encrypt(mrn),
            mrn_search_hash=compute_patient_search_hash(mrn),
            ssn_encrypted=_encrypt(ssn) if ssn else None,
            ssn_search_hash=compute_patient_search_hash(ssn) if ssn else None,
            first_name_encrypted=_encrypt(first_name),
            last_name_encrypted=_encrypt(last_name),
            date_of_birth_encrypted=_encrypt(dob),
            phone_encrypted=_encrypt(phone) if phone else None,
            email_encrypted=_encrypt(email) if email else None,
            address_encrypted=_encrypt(address) if address else None,
            gender=gender,
        )

        logger.info(
            "Patient created: id=%s mrn_hash=%s",
            patient.id,
            patient.mrn_search_hash,
        )
        return patient

    def to_representation(self, instance):
        """Return a masked representation after creation."""
        mrn_plain = _decrypt(instance.mrn_encrypted)
        return {
            "id": str(instance.id),
            "mrn": mask_patient_field(mrn_plain, "default"),
            "name": _masked_name(instance),
            "gender": instance.gender,
            "is_active": instance.is_active,
            "created_at": instance.created_at.isoformat(),
        }


# ── PatientListSerializer ───────────────────────────────────────────

class PatientListSerializer(serializers.Serializer):
    """Read-only masked representation for patient lists."""

    def to_representation(self, instance):
        mrn_plain = _decrypt(instance.mrn_encrypted)
        dob_plain = _decrypt(instance.date_of_birth_encrypted)
        return {
            "id": str(instance.id),
            "mrn": mask_patient_field(mrn_plain, "default"),
            "name": _masked_name(instance),
            "date_of_birth": mask_patient_field(dob_plain, "dob"),
            "gender": instance.gender,
            "is_active": instance.is_active,
        }


# ── PatientDetailSerializer ─────────────────────────────────────────

class PatientDetailSerializer(serializers.Serializer):
    """
    Full patient detail.  If the request context contains an active
    break-glass session, fields are returned unmasked.
    """

    def to_representation(self, instance):
        request = self.context.get("request")
        unmasked = self.context.get("break_glass_active", False)

        mrn = _decrypt(instance.mrn_encrypted)
        first_name = _decrypt(instance.first_name_encrypted)
        last_name = _decrypt(instance.last_name_encrypted)
        dob = _decrypt(instance.date_of_birth_encrypted)
        ssn = _decrypt(instance.ssn_encrypted) if instance.ssn_encrypted else ""
        phone = _decrypt(instance.phone_encrypted) if instance.phone_encrypted else ""
        email = _decrypt(instance.email_encrypted) if instance.email_encrypted else ""
        address = _decrypt(instance.address_encrypted) if instance.address_encrypted else ""

        if unmasked:
            return {
                "id": str(instance.id),
                "mrn": mrn,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": dob,
                "ssn": ssn,
                "gender": instance.gender,
                "phone": phone,
                "email": email,
                "address": address,
                "is_active": instance.is_active,
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
            }

        return {
            "id": str(instance.id),
            "mrn": mask_patient_field(mrn, "default"),
            "first_name": mask_patient_field(first_name, "name"),
            "last_name": mask_patient_field(last_name, "name"),
            "date_of_birth": mask_patient_field(dob, "dob"),
            "ssn": mask_patient_field(ssn, "ssn") if ssn else "",
            "gender": instance.gender,
            "phone": mask_patient_field(phone, "phone") if phone else "",
            "email": mask_patient_field(email, "email") if email else "",
            "address": mask_patient_field(address, "default") if address else "",
            "is_active": instance.is_active,
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat(),
        }


# ── PatientSearchSerializer ─────────────────────────────────────────

class PatientSearchSerializer(serializers.Serializer):
    """
    Input serializer for patient search.
    Computes HMAC of the query and searches by mrn or ssn hash.
    """

    q = serializers.CharField(min_length=1, max_length=100)

    def search(self):
        query = self.validated_data["q"]
        search_hash = compute_patient_search_hash(query)

        patients = Patient.objects.filter(
            models_q_mrn_or_ssn(search_hash),
            is_active=True,
        )
        return patients


def models_q_mrn_or_ssn(search_hash: str):
    """Build a Q object for searching by MRN or SSN hash."""
    from django.db.models import Q

    return Q(mrn_search_hash=search_hash) | Q(ssn_search_hash=search_hash)


# ── BreakGlassSerializer ────────────────────────────────────────────

class BreakGlassSerializer(serializers.Serializer):
    """
    Input for initiating a break-glass access event.
    """

    justification = serializers.CharField(min_length=20)
    justification_category = serializers.ChoiceField(
        choices=[c[0] for c in BreakGlassLog.JUSTIFICATION_CATEGORIES],
    )


# ── PatientUpdateSerializer ─────────────────────────────────────────

class PatientUpdateSerializer(serializers.Serializer):
    """
    Accepts optional plaintext fields.  Re-encrypts any changed
    fields and updates HMAC search hashes when applicable.
    """

    mrn = serializers.CharField(max_length=20, required=False)
    ssn = serializers.CharField(max_length=11, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        changed_fields = {}

        if "mrn" in validated_data:
            new_mrn = validated_data["mrn"]
            new_hash = compute_patient_search_hash(new_mrn)
            if new_hash != instance.mrn_search_hash:
                if Patient.objects.filter(mrn_search_hash=new_hash).exclude(pk=instance.pk).exists():
                    raise serializers.ValidationError(
                        {"mrn": "A patient with this MRN already exists."}
                    )
                changed_fields["mrn"] = True
                instance.mrn_encrypted = _encrypt(new_mrn)
                instance.mrn_search_hash = new_hash

        if "ssn" in validated_data:
            new_ssn = validated_data["ssn"]
            changed_fields["ssn"] = True
            if new_ssn:
                instance.ssn_encrypted = _encrypt(new_ssn)
                instance.ssn_search_hash = compute_patient_search_hash(new_ssn)
            else:
                instance.ssn_encrypted = None
                instance.ssn_search_hash = None

        if "first_name" in validated_data:
            changed_fields["first_name"] = True
            instance.first_name_encrypted = _encrypt(validated_data["first_name"])

        if "last_name" in validated_data:
            changed_fields["last_name"] = True
            instance.last_name_encrypted = _encrypt(validated_data["last_name"])

        if "date_of_birth" in validated_data:
            changed_fields["date_of_birth"] = True
            instance.date_of_birth_encrypted = _encrypt(
                str(validated_data["date_of_birth"])
            )

        if "gender" in validated_data:
            changed_fields["gender"] = True
            instance.gender = validated_data["gender"]

        if "phone" in validated_data:
            changed_fields["phone"] = True
            phone = validated_data["phone"]
            instance.phone_encrypted = _encrypt(phone) if phone else None

        if "email" in validated_data:
            changed_fields["email"] = True
            email = validated_data["email"]
            instance.email_encrypted = _encrypt(email) if email else None

        if "address" in validated_data:
            changed_fields["address"] = True
            address = validated_data["address"]
            instance.address_encrypted = _encrypt(address) if address else None

        if "is_active" in validated_data:
            changed_fields["is_active"] = True
            instance.is_active = validated_data["is_active"]

        instance.save()

        logger.info(
            "Patient updated: id=%s fields=%s",
            instance.id,
            list(changed_fields.keys()),
        )
        return instance, list(changed_fields.keys())

    def to_representation(self, instance):
        """Return masked representation after update."""
        return PatientDetailSerializer(
            instance, context=self.context
        ).data
