# MedRights Patient Media & Consent Portal

Offline clinical portal for managing patient Master Patient Index (MPI) records, patient-facing artwork with originality tracking, time-bound consents, offline manual financials, and tamper-evident audit trails. Fully containerized with zero external dependencies.

## Prerequisites

- Docker Desktop (v24+)
- Docker Compose (v2.20+)
- Python 3 (for secret generation commands only; alternatively, use any random string generator)

## Quick Start

1. Generate and export all required secrets:

```bash
export MEDRIGHTS_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
export MEDRIGHTS_MASTER_KEY=$(python3 -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())")
export MYSQL_ROOT_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
export MYSQL_APP_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
```

Alternative without Python:

```bash
# Alternative without Python:
export MEDRIGHTS_SECRET_KEY=$(openssl rand -base64 50)
export MEDRIGHTS_MASTER_KEY=$(openssl rand -base64 32)
export MYSQL_ROOT_PASSWORD=$(openssl rand -base64 24)
export MYSQL_APP_PASSWORD=$(openssl rand -base64 24)
```

2. Start the services:

```bash
docker compose up --build
```

3. First-run setup (create the initial admin user):

```bash
docker compose exec backend python manage.py seed_initial_data --admin-password <YOUR_SECURE_PASSWORD>
```

Additional role users (front desk, clinician, compliance) should be created by the admin via the UI or API after initial setup.

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React SPA (Nginx) |
| Backend API | http://localhost:8000/api/v1/ | Django REST API |
| Health Check | http://localhost:8000/api/v1/health/ | System health status |
| MySQL | localhost:3306 | Database |
| Redis | localhost:6379 | Celery broker |

## Testing

```bash
./run_tests.sh
```

This runs:
1. **Backend unit + integration tests** (pytest, self-contained with SQLite)
2. **Frontend unit tests** (Vitest, self-contained in Node container)
3. **E2E tests** (Playwright, requires running stack -- skipped if stack is not up)

To include E2E tests, start the stack first:
```bash
docker compose up -d
docker compose exec backend python manage.py seed_initial_data --admin-password <password>
./run_tests.sh
```

## Architecture

```
Frontend (React 18 + TypeScript + shadcn/ui + Vite)
    |
    | HTTP (via Nginx reverse proxy)
    |
Backend (Django 5 + DRF, Hexagonal Architecture)
    |
    +-- Domain Layer (pure Python business logic)
    +-- Infrastructure (ORM, encryption, file storage)
    +-- API Layer (DRF serializers, views)
    |
    +-- MySQL 8.0 (encrypted patient data, partitioned audit log)
    +-- Redis (Celery broker)
    +-- Celery Worker (async tasks: auto-close, reconciliation, reports)
    +-- Celery Beat (scheduled tasks)
```

### Backend Structure (Hexagonal)
- `domain/` -- Pure Python business logic, no Django imports
- `infrastructure/` -- Django-coupled adapters (ORM, encryption, middleware)
- `apps/` -- Django apps with DRF views and serializers (API layer)

### Frontend Structure (Feature-based)
- `src/api/` -- Axios client, endpoint functions, TypeScript types
- `src/contexts/` -- Auth, notifications
- `src/components/` -- Shared UI (shadcn/ui), layout, domain components
- `src/features/` -- Vertical slices: auth, patients, media, financials, etc.

## User Roles

| Role | Access |
|------|--------|
| **Front Desk** | Patient registration, MPI search, orders, payments, media upload |
| **Clinician** | Patient records, attach media to patient materials |
| **Compliance** | Break-glass review, infringement reports, disputes, audit logs |
| **Admin** | All above + user management, bulk export, system config, audit purge |

## API Endpoints

### Authentication
- `POST /api/v1/auth/login/` -- Login with username/password
- `POST /api/v1/auth/logout/` -- End session
- `GET /api/v1/auth/session/` -- Current session info
- `POST /api/v1/auth/session/refresh/` -- Reset idle timer
- `POST /api/v1/auth/change-password/` -- Change password

### Patients (MPI)
- `GET /api/v1/patients/?q=<term>` -- Search patients (masked results)
- `POST /api/v1/patients/create/` -- Create patient record
- `GET /api/v1/patients/{id}/` -- Get patient (masked)
- `PATCH /api/v1/patients/{id}/update/` -- Update patient fields
- `POST /api/v1/patients/{id}/break-glass/` -- Request unmasked access

### Consents
- `GET /api/v1/patients/{id}/consents/` -- List consents
- `POST /api/v1/patients/{id}/consents/` -- Create consent
- `POST /api/v1/patients/{id}/consents/{id}/revoke/` -- Revoke consent

### Media
- `POST /api/v1/media/upload/` -- Upload with fingerprinting
- `POST /api/v1/media/{id}/watermark/` -- Apply server-side watermark
- `POST /api/v1/media/{id}/repost/authorize/` -- Authorize repost with citation
- `POST /api/v1/media/infringement/` -- File infringement report

### Financials
- `POST /api/v1/financials/orders/` -- Create order
- `POST /api/v1/financials/orders/{id}/payments/` -- Record payment
- `POST /api/v1/financials/orders/{id}/refunds/` -- Initiate refund
- `GET /api/v1/financials/reconciliation/` -- View reconciliation

### Audit
- `GET /api/v1/audit/entries/` -- Search audit log
- `POST /api/v1/audit/verify-chain/` -- Verify tamper-evident chain

### Reports
- `POST /api/v1/reports/subscriptions/` -- Create report subscription
- `GET /api/v1/reports/outbox/` -- View outbox dashboard
- `GET /api/v1/reports/dashboard/` -- Runtime status dashboard

### Admin
- `GET /api/v1/users/` -- List users (admin only)
- `POST /api/v1/users/{id}/disable/` -- Disable user (admin + sudo)
- `POST /api/v1/sudo/acquire/` -- Acquire sudo-mode token
- `GET /api/v1/workstations/` -- List blacklisted workstations
- `POST /api/v1/workstations/{id}/unblock/` -- Unblock workstation (admin + sudo)

### Bulk Export
- `POST /api/v1/export/patients/` -- Export patient records as CSV (admin + sudo)
- `POST /api/v1/export/media/` -- Export media metadata as CSV (admin + sudo)
- `POST /api/v1/export/financials/` -- Export financial records as CSV (admin + sudo)

## Security

- **Passwords**: Argon2id hashing
- **Sessions**: 15-minute idle timeout, 8-hour absolute limit
- **Encryption**: AES-256-GCM for patient PII, HMAC-SHA256 for search indexes
- **Throttling**: 5 failed logins / 10 min / workstation, auto-blacklist after 3 lockouts
- **Audit**: Tamper-evident SHA-256 hash chain, 180-day searchable, 7-year archive
- **Admin Actions**: Sudo-mode (re-enter password) required for dangerous operations
- **No Deletion**: Financial records use compensating entries, never DELETE

### Data Isolation Model
MedRights is a single-tenant system designed for one clinic per deployment. All patient, financial, and media data belongs to one organization. Access control is enforced through role-based permissions (Front Desk, Clinician, Compliance, Admin), not multi-tenant scoping. Each clinic deployment runs on its own dedicated infrastructure.

## Operations

### Backup
- Schedule `mysqldump` daily on the host or via a cron container
- Also back up the `media_storage` Docker volume
- Store backups on a separate physical drive or NAS

### TLS
This system is designed for offline LAN deployment without TLS. If deployed on a network where traffic may be intercepted, add a reverse proxy with TLS termination and update `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` to `True`.
