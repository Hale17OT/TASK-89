# MedRights API Specification (v1)

Base URL: `/api/v1/`

## Conventions
- Auth model: session/cookie-based authentication.
- Content type: `application/json` unless otherwise noted.
- Time format: ISO 8601 UTC timestamps.
- IDs: opaque integer or UUID values (implementation-defined).
- Pagination: endpoint-specific; list responses may include `count`, `next`, `previous`, `results`.

## Authentication and Authorization

### Login
- `POST /auth/login/`
- Body:
```json
{
  "username": "string",
  "password": "string"
}
```
- Success: `200 OK`, session established.

### Logout
- `POST /auth/logout/`
- Success: `204 No Content`.

### Session Info
- `GET /auth/session/`
- Returns current user, role set, timeout metadata.

### Session Refresh
- `POST /auth/session/refresh/`
- Extends idle timer when allowed.

### Change Password
- `POST /auth/change-password/`
- Body:
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

## Health

### Health Check
- `GET /health/`
- Returns service status and dependency readiness.

## Patients (MPI)

### Search Patients
- `GET /patients/?q=<term>`
- Returns masked results unless elevated access applies.

### Create Patient
- `POST /patients/create/`
- Body (example):
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "dob": "1988-02-15",
  "phone": "+1-555-0100",
  "email": "jane.doe@example.local"
}
```

### Get Patient
- `GET /patients/{patient_id}/`
- Returns masked or unmasked fields based on policy/elevation.

### Update Patient
- `PATCH /patients/{patient_id}/update/`
- Partial update of mutable patient fields.

### Break-Glass Request
- `POST /patients/{patient_id}/break-glass/`
- Body (example):
```json
{
  "reason": "Urgent treatment review"
}
```
- Emits audit event and grants controlled temporary unmasking per policy.

## Consents

### List Consents
- `GET /patients/{patient_id}/consents/`

### Create Consent
- `POST /patients/{patient_id}/consents/`
- Body (example):
```json
{
  "consent_type": "media_use",
  "effective_at": "2026-04-01T00:00:00Z",
  "expires_at": "2027-04-01T00:00:00Z",
  "notes": "Signed in clinic"
}
```

### Revoke Consent
- `POST /patients/{patient_id}/consents/{consent_id}/revoke/`
- Body (optional):
```json
{
  "reason": "Patient request"
}
```

## Media

### Upload Media
- `POST /media/upload/`
- Multipart or JSON metadata + binary upload (implementation-specific).
- Computes/stores fingerprint metadata.

### Apply Watermark
- `POST /media/{media_id}/watermark/`
- Body (example):
```json
{
  "label": "Clinic Internal",
  "position": "bottom_right"
}
```

### Authorize Repost
- `POST /media/{media_id}/repost/authorize/`
- Body (example):
```json
{
  "target": "patient_portal",
  "citation": "Original source + date"
}
```

### File Infringement Report
- `POST /media/infringement/`
- Body (example):
```json
{
  "media_id": 123,
  "reported_by": "compliance_user",
  "details": "Suspected unauthorized external use"
}
```

## Financials

### Create Order
- `POST /financials/orders/`
- Body (example):
```json
{
  "patient_id": 42,
  "currency": "USD",
  "items": [
    { "code": "CONSULT", "quantity": 1, "unit_price": "120.00" }
  ]
}
```

### Record Payment
- `POST /financials/orders/{order_id}/payments/`
- Body (example):
```json
{
  "amount": "120.00",
  "method": "cash",
  "received_at": "2026-04-12T13:40:00Z"
}
```

### Initiate Refund
- `POST /financials/orders/{order_id}/refunds/`
- Body (example):
```json
{
  "amount": "20.00",
  "reason": "Billing correction"
}
```

### Reconciliation View
- `GET /financials/reconciliation/`
- Returns period summaries and mismatch indicators.

## Audit

### List/Search Audit Entries
- `GET /audit/entries/`
- Supports filtering by actor, action, date range, and object scope.

### Verify Audit Chain
- `POST /audit/verify-chain/`
- Runs integrity verification for hash-linked entries.

## Reports

### Create Subscription
- `POST /reports/subscriptions/`

### Outbox Dashboard
- `GET /reports/outbox/`

### Runtime Dashboard
- `GET /reports/dashboard/`

## Admin and Governance

### List Users
- `GET /users/` (admin only)

### Disable User
- `POST /users/{user_id}/disable/` (admin + sudo-mode)

### Acquire Sudo Token
- `POST /sudo/acquire/`
- Body:
```json
{
  "password": "string"
}
```

### List Workstations
- `GET /workstations/` (admin only)

### Unblock Workstation
- `POST /workstations/{workstation_id}/unblock/` (admin + sudo-mode)

## Bulk Export

### Export Patients CSV
- `POST /export/patients/` (admin + sudo-mode)

### Export Media CSV
- `POST /export/media/` (admin + sudo-mode)

### Export Financials CSV
- `POST /export/financials/` (admin + sudo-mode)

## Common Error Responses
- `400 Bad Request`: validation failure.
- `401 Unauthorized`: missing/invalid session.
- `403 Forbidden`: authenticated but lacks role/sudo/elevation.
- `404 Not Found`: resource does not exist or not visible.
- `409 Conflict`: state conflict (e.g., duplicate action, invalid transition).
- `429 Too Many Requests`: throttled/lockout policy triggered.
- `500 Internal Server Error`: unexpected server failure.

## Auditability Requirements
- Sensitive endpoints MUST emit audit events with actor, timestamp, action, target, and outcome.
- Break-glass, sudo-mode acquisition, user/workstation admin actions, and export operations MUST be auditable.
- Financial endpoints MUST preserve append-only semantics (no destructive deletion).
