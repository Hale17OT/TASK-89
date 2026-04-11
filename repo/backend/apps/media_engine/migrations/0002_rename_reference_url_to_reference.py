"""Rename reference_url to reference and change from URLField to CharField."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("media_engine", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="infringementreport",
            old_name="reference_url",
            new_name="reference",
        ),
        migrations.AlterField(
            model_name="infringementreport",
            name="reference",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]
