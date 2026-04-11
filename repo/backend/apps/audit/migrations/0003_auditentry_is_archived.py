"""Add is_archived field to AuditEntry for 180-day archival enforcement."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0002_auditarchivesegment"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditentry",
            name="is_archived",
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
