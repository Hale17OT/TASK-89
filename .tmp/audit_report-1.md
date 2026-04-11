# MedRights Delivery Acceptance + Architecture Audit (Static-Only)

Date: 2026-04-11

## 1. Verdict
- Overall conclusion: **Partial Pass**

## 2. Scope and Static Verification Boundary
- Reviewed: repository docs/config, Django settings/URLs/middleware/apps, React routes/pages/API clients, backend/frontend/e2e test code, and task scheduling definitions (`README.md:1`, `backend/medrights/urls.py:4`, `frontend/src/router.tsx:33`, `backend/tests/integration/test_auth_api.py:1`, `e2e/playwright.config.ts:1`).
- Not reviewed in depth: generated artifacts and vendored dependencies (`frontend/dist`, `frontend/node_modules`) and binary caches (`__pycache__`).
- Intentionally not executed: app startup, Docker, DB/Celery workers, unit/integration/e2e tests, browser flows.
- Manual verification required for runtime-only claims: timeout behavior in live sessions, Celery-driven auto-close/retry schedules, outbox file delivery to real print/shared targets, and UI rendering/accessibility in browsers (`backend/apps/financials/tasks.py:17`, `backend/apps/reports/tasks.py:471`, `frontend/src/features/reports/pages/OutboxDashboardPage.tsx:41`).

## 3. Repository / Requirement Mapping Summary
- Prompt core goal mapped: offline clinic portal with MPI, consent lifecycle, media originality/watermarking/repost authorization, infringement disputes, report subscriptions/outbox, offline financial posting/reconciliation, and strong audit/security controls.
- Main implementation areas mapped: Django apps (`accounts`, `mpi`, `consent`, `media_engine`, `financials`, `audit`, `reports`) and feature-sliced React frontend (`patients`, `media`, `infringements`, `financials`, `reports`, `admin`) (`backend/medrights/settings/base.py:42`, `frontend/src/router.tsx:12`).
- Major constraints mapped: local auth/session controls, Argon2 hashing, AES-GCM encryption service, workstation throttling/blacklist, sudo-confirmed admin actions, and hash-chained audit model (`backend/medrights/settings/base.py:112`, `backend/infrastructure/encryption/service.py:63`, `backend/infrastructure/middleware/throttle.py:13`, `backend/apps/accounts/views_export.py:28`, `backend/apps/audit/models.py:91`).

## 4. Section-by-section Review

### 1. Hard Gates
- **1.1 Documentation and static verifiability**
  - Conclusion: **Pass**
  - Rationale: README provides startup, roles, endpoint map, architecture, and test commands; settings/URL structure align with docs.
  - Evidence: `README.md:11`, `README.md:111`, `backend/medrights/urls.py:5`, `backend/medrights/settings/base.py:33`
  - Manual verification note: Docker/stack behavior still requires manual runtime verification.
- **1.2 Material deviation from Prompt**
  - Conclusion: **Partial Pass**
  - Rationale: Core domain is implemented, but consent enforcement on media reuse is incomplete (revoked-only check; no expiration/effective/scope checks), which weakens authorized reuse semantics.
  - Evidence: `backend/apps/media_engine/views.py:191`, `backend/apps/media_engine/views.py:469`, `backend/apps/media_engine/serializers.py:115`, `backend/apps/consent/models.py:34`

### 2. Delivery Completeness
- **2.1 Core explicit requirements coverage**
  - Conclusion: **Partial Pass**
  - Rationale: Most required modules and flows exist (MPI, break-glass, consents, watermark/originality, disputes, outbox, financials). Gap: media usage paths do not fully enforce time-bound consent rules.
  - Evidence: `backend/apps/mpi/views.py:27`, `backend/apps/consent/views.py:39`, `backend/apps/media_engine/views.py:52`, `backend/apps/reports/views.py:30`, `backend/apps/financials/views.py:67`, `backend/apps/media_engine/views.py:191`
- **2.2 End-to-end 0→1 deliverable vs partial demo**
  - Conclusion: **Pass**
  - Rationale: Full project structure, backend/frontend apps, migrations/tests/docs are present rather than a code fragment.
  - Evidence: `README.md:72`, `backend/apps/`, `frontend/src/`, `backend/tests/integration/test_reports_api.py:1`

### 3. Engineering and Architecture Quality
- **3.1 Structure and module decomposition**
  - Conclusion: **Pass**
  - Rationale: Reasonable separation of concerns across apps, middleware, domain services, serializers, and views.
  - Evidence: `backend/medrights/settings/base.py:42`, `backend/domain/services/patient_service.py:1`, `backend/apps/media_engine/views.py:1`
- **3.2 Maintainability/extensibility**
  - Conclusion: **Partial Pass**
  - Rationale: Overall maintainable structure, but some compliance-critical behavior is split between API and async tasks without consistent audit write paths.
  - Evidence: `backend/infrastructure/middleware/audit_logging.py:13`, `backend/apps/financials/tasks.py:38`, `backend/apps/financials/views.py:100`

### 4. Engineering Details and Professionalism
- **4.1 Error handling, logging, validation, API design**
  - Conclusion: **Partial Pass**
  - Rationale: Good baseline (custom error handler, serializers, role guards, structured logging), but compliance-grade audit expectations are not uniformly met for non-request financial mutations.
  - Evidence: `backend/infrastructure/exceptions.py:11`, `backend/apps/accounts/permissions.py:5`, `backend/apps/financials/tasks.py:38`, `backend/apps/audit/service.py:28`
- **4.2 Real product/service shape vs demo**
  - Conclusion: **Pass**
  - Rationale: Includes operational concerns (Celery schedules, archival, throttling, outbox retry), not only UI demo screens.
  - Evidence: `backend/medrights/celery.py:12`, `backend/apps/audit/tasks.py:54`, `backend/apps/reports/tasks.py:565`

### 5. Prompt Understanding and Requirement Fit
- **5.1 Business goal/constraints fit**
  - Conclusion: **Partial Pass**
  - Rationale: Strong alignment overall, but consent-governed authorized media reuse is under-enforced in key usage endpoints.
  - Evidence: `backend/apps/media_engine/views.py:191`, `backend/apps/media_engine/views.py:469`, `backend/apps/consent/serializers.py:40`

### 6. Aesthetics (frontend)
- **6.1 Visual/interaction quality**
  - Conclusion: **Cannot Confirm Statistically**
  - Rationale: Component hierarchy and states exist, but visual quality, responsive behavior, and rendering fidelity require browser execution.
  - Evidence: `frontend/src/features/auth/pages/LoginPage.tsx:102`, `frontend/src/features/reports/pages/OutboxDashboardPage.tsx:157`, `frontend/src/styles/globals.css:6`
  - Manual verification note: Verify desktop/mobile layouts, spacing/contrast, and interaction feedback in a running browser.

## 5. Issues / Suggestions (Severity-Rated)

- **Severity: High**
  - Title: Consent lifecycle is not fully enforced for media usage/reuse
  - Conclusion: **Fail**
  - Evidence: `backend/apps/media_engine/views.py:191`, `backend/apps/media_engine/views.py:469`, `backend/apps/media_engine/serializers.py:115`, `backend/apps/consent/models.py:34`
  - Impact: Media can be attached/used without verifying active, non-expired, scope-appropriate consent; this undermines the prompt’s authorized reuse and time-bound consent controls.
  - Minimum actionable fix: Enforce consent validity checks (effective/expiration/revoked + scope + patient-consent consistency) in upload/link/download and any external-use media path.

- **Severity: High**
  - Title: Financial auto-adjustments are not written to tamper-evident audit log
  - Conclusion: **Fail**
  - Evidence: `backend/apps/financials/tasks.py:38`, `backend/infrastructure/middleware/audit_logging.py:28`, `backend/apps/audit/service.py:28`
  - Impact: Order status changes done by scheduled tasks (e.g., auto-close) are only normal logs, not hash-chained audit entries; this weakens "fully audited" financial adjustments.
  - Minimum actionable fix: Call `create_audit_entry` from financial async tasks for state transitions and key field changes.

- **Severity: Medium**
  - Title: Revocation UX deviates from stated one-click revocation
  - Conclusion: **Partial Fail**
  - Evidence: `frontend/src/features/patients/components/ConsentCard.tsx:102`, `frontend/src/features/patients/components/ConsentCard.tsx:144`, `backend/apps/consent/serializers.py:111`
  - Impact: Workflow requires extra form input and confirmation; does not match strict "one-click revocation" wording.
  - Minimum actionable fix: Offer a direct one-click revoke action (with optional post-action notes flow), or update requirement/doc wording to match current compliance workflow.

- **Severity: Medium**
  - Title: Public client-error logging endpoint can still ingest sensitive free-text values
  - Conclusion: **Suspected Risk**
  - Evidence: `backend/apps/audit/views_client_logs.py:44`, `backend/apps/audit/views_client_logs.py:141`, `backend/apps/audit/views_client_logs.py:170`
  - Impact: Endpoint strips sensitive keys but not sensitive values embedded in message/stack text; PHI/secrets could be persisted if frontend sends them.
  - Minimum actionable fix: Add value-pattern redaction for PII/secret formats and stricter truncation/allowlist for `message`/`stack`.

- **Severity: Low**
  - Title: Audit coverage is inconsistent across read-heavy/reporting endpoints
  - Conclusion: **Partial Fail**
  - Evidence: `backend/apps/reports/views.py:216`, `backend/apps/media_engine/views.py:99`, `backend/infrastructure/middleware/audit_logging.py:15`
  - Impact: Some operationally relevant reads/actions are not entered into audit chain, reducing review completeness.
  - Minimum actionable fix: Add `_audit_context` to selected report/media read endpoints where compliance traceability is required.

## 6. Security Review Summary
- **Authentication entry points**: **Pass** - Local login/logout/session/change-password endpoints exist, with Argon2 hashing and session middleware controls (`backend/apps/accounts/urls.py:7`, `backend/medrights/settings/base.py:112`, `backend/infrastructure/middleware/session_timeout.py:31`).
- **Route-level authorization**: **Pass** - DRF role permissions are consistently used on major endpoint groups (`backend/apps/accounts/permissions.py:5`, `backend/apps/reports/views.py:31`, `backend/apps/media_engine/views.py:525`).
- **Object-level authorization**: **Partial Pass** - Patient/consent object existence checks are present, but consent-object semantics are not fully validated in media reuse paths (`backend/apps/consent/views.py:103`, `backend/apps/media_engine/serializers.py:115`, `backend/apps/media_engine/views.py:469`).
- **Function-level authorization**: **Pass** - Sensitive admin actions enforce sudo token + confirmation checks (`backend/apps/accounts/views_users.py:143`, `backend/apps/accounts/views_export.py:28`, `backend/apps/audit/views.py:169`).
- **Tenant/user data isolation**: **Pass (single-tenant model)** - Explicit single-tenant architecture and RBAC model are documented and reflected in code.
  - Evidence: `backend/medrights/settings/base.py:13`, `README.md:175`
- **Admin/internal/debug protection**: **Partial Pass** - Most admin endpoints are restricted; health endpoint is public but minimized for non-admins; client-log endpoint is intentionally public with throttling.
  - Evidence: `backend/apps/health/views.py:14`, `backend/apps/health/views.py:91`, `backend/apps/audit/views_client_logs.py:44`

## 7. Tests and Logging Review
- **Unit tests**: **Pass** - Domain/encryption/audit chain and archival unit tests exist and target core utility/security logic (`backend/tests/unit/test_encryption.py:1`, `backend/tests/unit/test_audit_chain.py:1`).
- **API/integration tests**: **Partial Pass** - Broad endpoint/role coverage exists, but key risk cases (consent expiry enforcement in media paths, async-task audit entry coverage) are missing (`backend/tests/integration/test_media_api.py:182`, `backend/tests/integration/test_financials_api.py:45`).
- **Logging categories / observability**: **Pass** - Named loggers, JSON formatter, request ID middleware, and structured audit service are present (`backend/medrights/settings/base.py:247`, `backend/infrastructure/middleware/request_id.py:15`, `backend/apps/audit/service.py:126`).
- **Sensitive-data leakage risk in logs/responses**: **Partial Pass** - API error responses are sanitized; however public client error ingestion may persist sensitive free-text values.
  - Evidence: `backend/infrastructure/exceptions.py:47`, `backend/apps/audit/views_client_logs.py:141`, `backend/apps/audit/views_client_logs.py:185`

## 8. Test Coverage Assessment (Static Audit)

### 8.1 Test Overview
- Unit tests exist under `backend/tests/unit/` using `pytest` + `pytest-django` (`backend/pytest.ini:1`, `backend/tests/unit/test_domain_services.py:1`).
- Backend integration tests exist under `backend/tests/integration/` with DRF `APIClient` and role fixtures (`backend/tests/conftest.py:83`, `backend/tests/integration/test_authorization.py:8`).
- Frontend unit tests exist with Vitest + jsdom (`frontend/package.json:10`, `frontend/vitest.config.ts:7`).
- E2E tests exist with Playwright but require running stack; static audit only (`e2e/playwright.config.ts:3`, `README.md:63`).
- Test command documentation is present (`README.md:54`, `run_tests.sh:9`).

### 8.2 Coverage Mapping Table

| Requirement / Risk Point | Mapped Test Case(s) | Key Assertion / Fixture / Mock | Coverage Assessment | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| Auth login/session/throttle | `backend/tests/integration/test_auth_api.py:30` | Login success/401/429/session checks (`backend/tests/integration/test_auth_api.py:33`) | basically covered | No explicit test for absolute timeout middleware branch | Add middleware-focused test for absolute timeout 401 reason=absolute |
| 401/403 route protection | `backend/tests/integration/test_authorization.py:22` | Parametrized unauthenticated GET/POST rejection (`backend/tests/integration/test_authorization.py:26`) | sufficient | Limited endpoint sample, not exhaustive | Add smoke matrix for all registered URL groups |
| MPI masked by default + break-glass | `backend/tests/integration/test_patient_api.py:66` | Masked SSN/name assertions and unmasked break-glass return (`backend/tests/integration/test_patient_api.py:72`, `backend/tests/integration/test_patient_api.py:96`) | sufficient | No explicit test for break-glass reviewability via audit list | Add audit-entry assertion after break-glass call |
| Consent create/revoke rules | `backend/tests/integration/test_consent_api.py:35` | Date validation + physical-copy revoke ack (`backend/tests/integration/test_consent_api.py:42`, `backend/tests/integration/test_consent_api.py:110`) | basically covered | No test for consent scope effect beyond export path | Add test linking consent scope to media usage authorization |
| Media originality/repost/watermark | `backend/tests/integration/test_media_api.py:101` | Duplicate upload -> reposted, download blocked when unauthorized repost (`backend/tests/integration/test_media_api.py:116`, `backend/tests/integration/test_media_api.py:197`) | basically covered | Missing tests for consent expiration/effective checks on attach/download | Add media tests for expired/revoked/invalid-scope consent |
| Financial create/pay/refund/no-delete | `backend/tests/integration/test_financials_api.py:45` | Order/pay/refund and delete-protection assertions (`backend/tests/integration/test_financials_api.py:48`, `backend/tests/integration/test_financials_api.py:138`) | basically covered | No tests for auto-close task + audit write | Add task-level test asserting order closed and audit entry created |
| Export sudo + consent filtering | `backend/tests/integration/test_export_api.py:47`, `backend/tests/integration/test_regression.py:94` | 403 without sudo, consent-scope inclusion/exclusion checks (`backend/tests/integration/test_export_api.py:50`, `backend/tests/integration/test_regression.py:104`) | sufficient | Missing negative tests for malformed confirm payloads per endpoint | Add validation tests for `confirm=false` across export endpoints |
| Reports/outbox RBAC and dashboard | `backend/tests/integration/test_reports_api.py:21` | Admin/compliance allowed, frontdesk/clinician denied (`backend/tests/integration/test_reports_api.py:73`) | basically covered | No integration tests of generate/deliver retry lifecycle via API | Add API-flow test for failed->retry->delivered transitions |
| Audit chain integrity | `backend/tests/unit/test_audit_chain.py:13` | Genesis/hash tamper detection assertions (`backend/tests/unit/test_audit_chain.py:22`, `backend/tests/unit/test_audit_chain.py:78`) | sufficient | No integration test proving key business events are always chained | Add integration tests asserting audit entries for key financial/media mutations |

### 8.3 Security Coverage Audit
- **Authentication**: basically covered (login success/failure, sudo acquisition, unauthenticated denial) (`backend/tests/integration/test_auth_api.py:30`, `backend/tests/integration/test_authorization.py:22`).
- **Route authorization**: sufficient for core role boundaries (`backend/tests/integration/test_authorization.py:45`, `backend/tests/integration/test_reports_api.py:73`).
- **Object-level authorization**: insufficient; tests do not deeply verify consent-object semantics across media usage paths.
  - Evidence: media tests focus repost/watermark/dispute, not consent validity (`backend/tests/integration/test_media_api.py:182`).
- **Tenant/data isolation**: not applicable in multi-tenant sense (single-tenant design); role-based tests present (`README.md:175`, `backend/tests/integration/test_authorization.py:42`).
- **Admin/internal protection**: basically covered for sudo and admin-only paths (`backend/tests/integration/test_admin_api.py:15`, `backend/tests/integration/test_export_api.py:47`).

### 8.4 Final Coverage Judgment
- **Partial Pass**
- Major risks covered: auth basics, RBAC route guards, core CRUD happy paths, export sudo checks, audit hash integrity.
- Uncovered risks: consent lifecycle enforcement in media reuse and audit completeness for async financial mutations; severe defects in these areas could still slip while current tests pass.

## 9. Final Notes
- This audit is evidence-based static analysis only; runtime behavior and integration reliability must be validated manually.
- The project is close to acceptance, but the two High findings (consent enforcement in media reuse and audit coverage for async financial mutations) are material for compliance/security intent in the prompt.
