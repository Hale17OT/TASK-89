"""Initial migration for consent app."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mpi", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Consent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("purpose", models.CharField(max_length=200)),
                ("granted_at", models.DateTimeField(auto_now_add=True)),
                ("effective_date", models.DateField()),
                ("expiration_date", models.DateField(blank=True, help_text="Null means the consent is indefinite.", null=True)),
                ("is_revoked", models.BooleanField(default=False)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("revocation_reason", models.TextField(blank=True, default="")),
                ("physical_copy_on_file", models.BooleanField(default=False)),
                ("physical_copy_warning_shown", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("granted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="granted_consents", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="consents", to="mpi.patient")),
                ("revoked_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="revoked_consents", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "consents",
                "ordering": ["-granted_at"],
            },
        ),
        migrations.CreateModel(
            name="ConsentScope",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("scope_type", models.CharField(choices=[("data_field", "Data Field"), ("action", "Action"), ("media_use", "Media Use"), ("third_party", "Third Party")], max_length=20)),
                ("scope_value", models.CharField(max_length=200)),
                ("consent", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scopes", to="consent.consent")),
            ],
            options={
                "db_table": "consent_scopes",
            },
        ),
    ]
