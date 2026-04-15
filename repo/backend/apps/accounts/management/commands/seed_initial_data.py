"""Management command to seed initial admin user, storage directories, and default policies."""
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import SystemPolicy, User


class Command(BaseCommand):
    help = "Create the initial admin user and storage directories for MedRights."

    STORAGE_DIRS = [
        "originals",
        "converted",
        "thumbnails",
        "exports",
        "temp",
    ]

    DEFAULT_POLICIES = [
        ("session_idle_timeout_seconds", 900, "Idle session timeout in seconds."),
        ("session_absolute_limit_seconds", 28800, "Absolute session lifetime in seconds."),
        ("max_failed_logins", 5, "Maximum failed login attempts before lockout."),
        ("lockouts_before_blacklist", 3, "Number of lockouts before workstation is blacklisted."),
        ("watermark_default_opacity", 0.35, "Default opacity for watermarks."),
        ("order_auto_close_minutes", 30, "Minutes before an unpaid order is auto-closed."),
        ("audit_archive_days", 180, "Days of audit entries kept in the searchable table."),
        ("audit_retention_years", 7, "Years to retain archived audit entries."),
        ("max_guest_profiles", 5, "Maximum guest profiles per session."),
    ]

    E2E_USERS = [
        ("admin", "admin", "System Administrator", True),
        ("frontdesk", "front_desk", "Front Desk User", False),
        ("clinician", "clinician", "Clinician User", False),
        ("compliance", "compliance", "Compliance Officer", False),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-password",
            type=str,
            default=None,
            help="Password for the initial admin user (required on first run).",
        )
        parser.add_argument(
            "--e2e",
            action="store_true",
            default=False,
            help="Create all role users for E2E testing with the given password.",
        )

    def handle(self, *args, **options):
        if options["e2e"]:
            self._create_e2e_users(options["admin_password"])
        else:
            self._create_admin_user(options["admin_password"])
        self._create_storage_dirs()
        self._seed_default_policies()
        self.stdout.write(self.style.SUCCESS("Seed data applied successfully."))

    def _create_e2e_users(self, password):
        if not password:
            raise CommandError(
                "Password required for E2E users. Run: "
                "manage.py seed_initial_data --e2e --admin-password <password>"
            )
        for username, role, full_name, is_staff in self.E2E_USERS:
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"  User '{username}' already exists -- skipped.")
                continue
            user = User.objects.create(
                username=username,
                role=role,
                full_name=full_name,
                is_active=True,
                is_staff=is_staff,
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(
                self.style.SUCCESS(f"  Created user '{username}' with role '{role}'")
            )

    def _create_admin_user(self, admin_password):
        if User.objects.filter(username="admin").exists():
            self.stdout.write("  User 'admin' already exists -- skipped.")
            return

        # No admin user exists yet; password is required.
        if not admin_password:
            raise CommandError(
                "Initial admin password required. Run: "
                "manage.py seed_initial_data --admin-password <password>"
            )

        user = User.objects.create(
            username="admin",
            role="admin",
            full_name="System Administrator",
            is_active=True,
            is_staff=True,
        )
        user.set_password(admin_password)
        user.save(update_fields=["password"])
        self.stdout.write(
            self.style.SUCCESS("  Created user 'admin' with role 'admin'")
        )

    def _seed_default_policies(self):
        created_count = 0
        for key, default_value, description in self.DEFAULT_POLICIES:
            _, created = SystemPolicy.objects.get_or_create(
                key=key,
                defaults={"value": default_value, "description": description},
            )
            if created:
                created_count += 1
        self.stdout.write(f"  Policies: {created_count} created, {len(self.DEFAULT_POLICIES) - created_count} already existed.")

    def _create_storage_dirs(self):
        storage_root = getattr(settings, "MEDRIGHTS_STORAGE_ROOT", os.path.join(settings.BASE_DIR, "storage"))
        for dirname in self.STORAGE_DIRS:
            dirpath = os.path.join(storage_root, dirname)
            os.makedirs(dirpath, exist_ok=True)
            self.stdout.write(f"  Ensured directory: {dirpath}")
