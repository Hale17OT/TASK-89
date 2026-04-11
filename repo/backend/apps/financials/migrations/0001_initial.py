"""Initial migration for financials app."""
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
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("order_number", models.CharField(db_index=True, max_length=20, unique=True)),
                ("status", models.CharField(choices=[("open", "Open"), ("paid", "Paid"), ("partial", "Partial"), ("closed_unpaid", "Closed Unpaid"), ("voided", "Voided"), ("refunded", "Refunded")], db_index=True, default="open", max_length=20)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=10)),
                ("tax_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("amount_paid", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("notes", models.TextField(blank=True, default="")),
                ("auto_close_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_orders", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="mpi.patient")),
            ],
            options={
                "db_table": "orders",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderLineItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("description", models.CharField(max_length=500)),
                ("quantity", models.IntegerField(default=1)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="line_items", to="financials.order")),
            ],
            options={
                "db_table": "order_line_items",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("payment_method", models.CharField(choices=[("cash", "Cash"), ("check", "Check")], max_length=10)),
                ("check_number", models.CharField(blank=True, default="", max_length=50)),
                ("reference_note", models.TextField(blank=True, default="")),
                ("is_compensating", models.BooleanField(default=False)),
                ("posted_at", models.DateTimeField(auto_now_add=True)),
                ("compensates", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="compensated_by", to="financials.payment")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="financials.order")),
                ("posted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="posted_payments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "payments",
                "ordering": ["-posted_at"],
            },
        ),
        migrations.CreateModel(
            name="CompensatingEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("parent_entry_id", models.UUIDField(blank=True, null=True)),
                ("parent_entry_type", models.CharField(choices=[("payment", "Payment"), ("compensating_entry", "Compensating Entry")], default="payment", max_length=20)),
                ("entry_type", models.CharField(choices=[("reversal", "Reversal"), ("adjustment", "Adjustment")], max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="compensating_entries", to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="compensating_entries", to="financials.order")),
            ],
            options={
                "db_table": "compensating_entries",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Refund",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("reason", models.TextField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("completed", "Completed"), ("denied", "Denied")], default="pending", max_length=20)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_refunds", to=settings.AUTH_USER_MODEL)),
                ("compensating_entry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="financials.compensatingentry")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="financials.order")),
                ("original_payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="financials.payment")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="requested_refunds", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "refunds",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DailyReconciliation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reconciliation_date", models.DateField(db_index=True, unique=True)),
                ("total_orders", models.IntegerField()),
                ("total_revenue", models.DecimalField(decimal_places=2, max_digits=12)),
                ("total_payments", models.DecimalField(decimal_places=2, max_digits=12)),
                ("total_refunds", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discrepancy", models.DecimalField(decimal_places=2, max_digits=12)),
                ("csv_file_path", models.CharField(max_length=500)),
                ("pdf_file_path", models.CharField(blank=True, default="", max_length=500)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("generated_by", models.CharField(max_length=50)),
                ("is_deferred", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "daily_reconciliation",
                "ordering": ["-reconciliation_date"],
            },
        ),
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                ("key", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("response_data", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
            ],
            options={
                "db_table": "idempotency_keys",
            },
        ),
    ]
