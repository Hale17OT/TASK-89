"""Initial migration for mpi app."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Patient",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("mrn_encrypted", models.BinaryField()),
                ("mrn_search_hash", models.CharField(db_index=True, max_length=64, unique=True)),
                ("ssn_encrypted", models.BinaryField(blank=True, null=True)),
                ("ssn_search_hash", models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ("first_name_encrypted", models.BinaryField()),
                ("last_name_encrypted", models.BinaryField()),
                ("date_of_birth_encrypted", models.BinaryField()),
                ("phone_encrypted", models.BinaryField(blank=True, null=True)),
                ("email_encrypted", models.BinaryField(blank=True, null=True)),
                ("address_encrypted", models.BinaryField(blank=True, null=True)),
                ("gender", models.CharField(blank=True, default="", max_length=20)),
                ("encryption_key_version", models.SmallIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "patients",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="BreakGlassLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("justification", models.TextField()),
                ("justification_category", models.CharField(choices=[("emergency", "Emergency"), ("treatment", "Treatment"), ("legal", "Legal"), ("admin", "Administrative"), ("other", "Other")], max_length=20)),
                ("accessed_at", models.DateTimeField(auto_now_add=True)),
                ("fields_accessed", models.JSONField(default=list, help_text="List of field names that were unmasked.")),
                ("ip_address", models.GenericIPAddressField()),
                ("workstation_id", models.CharField(max_length=100)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="break_glass_logs", to="mpi.patient")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="break_glass_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "break_glass_logs",
                "ordering": ["-accessed_at"],
            },
        ),
    ]
