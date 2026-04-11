# MedRights System Design

## Purpose
MedRights is an offline-first clinical portal for managing patient records, patient media, consent workflows, financial events, and tamper-evident audit history in a single clinic deployment.

## Goals
- Keep operations fully local (no external dependencies required for core workflows).
- Enforce strong role-based access control for front desk, clinician, compliance, and admin users.
- Protect sensitive data through encryption, masking, and strict access workflows (including break-glass and sudo-mode).
- Preserve legal and operational traceability with immutable-style financial handling and audit hash chaining.

## Non-Goals
- Multi-tenant SaaS support (single clinic per deployment).
- Real-time third-party integrations by default.
- Public internet exposure without an explicit TLS reverse proxy.

## High-Level Architecture
```text
React SPA (frontend, served by Nginx)
  -> Django REST API (backend)
       -> Domain layer (business rules)
       -> Infrastructure adapters (ORM, encryption, storage)
       -> API layer (serializers/views)
            -> MySQL (system of record)
            -> Redis (Celery broker)
            -> Celery worker + beat (async/scheduled jobs)
```

## Core Domains

### 1) Identity and Access
- Session-based authentication with idle and absolute session limits.
- Role-based permissions:
  - Front Desk: registration, MPI search, orders/payments, media upload.
  - Clinician: patient records and patient-linked media actions.
  - Compliance: infringement/dispute and audit-focused workflows.
  - Admin: full access, user/workstation control, exports, dangerous actions via sudo-mode.

### 2) Patient Registry (MPI)
- Patient records are searchable with masked responses by default.
- Break-glass flow allows controlled temporary access to unmasked data.
- Patient data fields are encrypted at rest where applicable.

### 3) Consent Management
- Consents are linked to patients and include validity windows.
- Revocation is explicit and auditable.
- Consent state gates media and downstream usage workflows.

### 4) Media and Originality
- Upload pipeline stores metadata and content fingerprints.
- Supports watermarking and repost authorization with citation controls.
- Infringement reports can be filed and reviewed through compliance workflows.

### 5) Financials
- Order -> payment -> refund modeled as append-only events.
- No hard deletes for financial records; use compensating entries.
- Reconciliation views support offline accounting operations.

### 6) Audit and Reporting
- Security-significant actions emit audit entries.
- Audit chain uses hash linkage for tamper evidence.
- Reporting supports subscriptions, outbox review, and dashboard status.

## Security Design
- Passwords: Argon2id hashing.
- Sessions: idle timeout + absolute max duration.
- Encryption: AES-256-GCM for protected patient fields.
- Search privacy: HMAC-SHA256 for searchable secure indexes.
- Abuse controls: login throttling and workstation blacklisting.
- Elevated actions: sudo-mode token required for high-risk operations.

## Data Lifecycle and Retention
- Audit data remains searchable for short-term operational windows and archived long-term.
- Financial records are retained as an event stream (including reversals/refunds).
- Media assets and backups should include both database dumps and media volume snapshots.

## Operational Model
- Containerized runtime via Docker Compose.
- Local LAN deployment assumed; add TLS proxy for untrusted networks.
- Health endpoint and scheduled jobs provide operational observability.

## Quality Attributes
- Security first: least privilege, masked defaults, explicit elevation paths.
- Traceability: immutable-style records and audit chaining.
- Reliability: async workers for deferred tasks and deterministic APIs.
- Maintainability: backend hexagonal boundaries + frontend feature-based organization.

## Tradeoffs
- Single-tenant model simplifies authorization and operations but limits centralized scaling.
- Offline-first deployment improves control and privacy but reduces out-of-box integration.
- Strong auditability increases schema/process complexity compared with CRUD-heavy designs.
