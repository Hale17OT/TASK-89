# Test Coverage Audit

## Backend Endpoint Inventory

Resolved from `backend/medrights/urls.py`, app `urls*.py`, and `@api_view(...)` declarations in each view module.

- Total resolved endpoints (`METHOD + PATH`): **79**
- Endpoint namespaces detected: `health`, `auth`, `patients`, `consents`, `media`, `financials`, `audit`, `reports`, `sudo`, `users`, `workstations`, `logs`, `export`, `policies`

## API Test Mapping Table

Legend:
- Covered = `yes` only when direct HTTP request to exact method+path was found.
- Test type = strongest observed for that endpoint.

| Endpoint | Covered | Test type | Test files | Evidence |
|---|---|---|---|---|
| `GET /api/v1/health/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestHealth::test_health_ok` |
| `GET /api/v1/auth/csrf/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuthCsrf::test_csrf_cookie` |
| `POST /api/v1/auth/login/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuthLogin::test_login_success` |
| `POST /api/v1/auth/logout/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuthLogout::test_logout_authenticated` |
| `GET /api/v1/auth/session/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuthSession::test_session_info` |
| `POST /api/v1/auth/session/refresh/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuthSession::test_session_refresh` |
| `POST /api/v1/auth/change-password/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestChangePassword::test_change_password_success` |
| `POST /api/v1/auth/remember-device/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRememberDevice::test_remember_device_post` |
| `GET /api/v1/auth/remember-device/prefill/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRememberDevice::test_remember_device_prefill_no_cookie` |
| `GET /api/v1/auth/guest-profiles/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles::test_guest_profile_list` |
| `POST /api/v1/auth/guest-profiles/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles::test_guest_profile_create` |
| `POST /api/v1/auth/guest-profiles/{uuid}/activate/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles::test_guest_profile_activate` |
| `GET /api/v1/auth/guest-profiles/{uuid}/recent-patients/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles::test_guest_recent_patients_list` |
| `POST /api/v1/auth/guest-profiles/{uuid}/recent-patients/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles::test_guest_recent_patients_post` |
| `GET /api/v1/patients/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPatientSearch::test_search_patients` |
| `POST /api/v1/patients/create/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPatientCreate::test_create_patient_admin` |
| `GET /api/v1/patients/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPatientDetail::test_detail` |
| `PATCH /api/v1/patients/{uuid}/update/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPatientUpdate::test_update_patient` |
| `POST /api/v1/patients/{uuid}/break-glass/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestBreakGlass::test_break_glass_success` |
| `GET /api/v1/patients/{patient_id}/consents/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestConsentListCreate::test_consent_list` |
| `POST /api/v1/patients/{patient_id}/consents/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestConsentListCreate::test_consent_create` |
| `GET /api/v1/patients/{patient_id}/consents/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestConsentDetail::test_consent_detail` |
| `POST /api/v1/patients/{patient_id}/consents/{uuid}/revoke/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestConsentRevoke::test_consent_revoke` |
| `POST /api/v1/media/upload/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestMediaUpload::test_upload_success` |
| `GET /api/v1/media/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestMediaList::test_media_list` |
| `GET /api/v1/media/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestMediaDetail::test_media_detail` |
| `GET /api/v1/media/{uuid}/download/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestMediaDownload::test_media_download` |
| `POST /api/v1/media/{uuid}/watermark/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestMediaWatermark::test_watermark` |
| `POST /api/v1/media/{uuid}/attach-patient/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestMediaAttachPatient::test_attach_patient` |
| `POST /api/v1/media/{uuid}/repost/authorize/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRepostAuthorize::test_repost_authorize_success` |
| `GET /api/v1/media/infringement/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestInfringementListCreate::test_infringement_list` |
| `POST /api/v1/media/infringement/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestInfringementListCreate::test_infringement_create` |
| `GET /api/v1/media/infringement/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestInfringementDetailUpdate::test_infringement_detail` |
| `PATCH /api/v1/media/infringement/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestInfringementDetailUpdate::test_infringement_update` |
| `GET /api/v1/financials/orders/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOrderListCreate::test_order_list` |
| `POST /api/v1/financials/orders/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOrderListCreate::test_order_create` |
| `GET /api/v1/financials/orders/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOrderDetail::test_order_detail` |
| `POST /api/v1/financials/orders/{uuid}/payments/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOrderPayment::test_order_payment` |
| `POST /api/v1/financials/orders/{uuid}/void/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOrderVoid::test_order_void` |
| `POST /api/v1/financials/orders/{uuid}/refunds/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRefundCreate::test_refund_create` |
| `GET /api/v1/financials/refunds/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRefundList::test_refund_list` |
| `POST /api/v1/financials/refunds/{uuid}/approve/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRefundApprove::test_refund_approve` |
| `POST /api/v1/financials/refunds/{uuid}/process/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRefundProcess::test_refund_process` |
| `GET /api/v1/financials/reconciliation/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestReconciliationList::test_reconciliation_list` |
| `GET /api/v1/financials/reconciliation/{date}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestReconciliationDetail::test_reconciliation_detail_success` |
| `GET /api/v1/financials/reconciliation/{date}/download/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestReconciliationDownload::test_reconciliation_download_success` |
| `GET /api/v1/audit/entries/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuditList::test_audit_list` |
| `GET /api/v1/audit/entries/{int}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuditDetail::test_audit_detail_not_found` |
| `POST /api/v1/audit/verify-chain/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuditVerifyChain::test_verify_chain` |
| `POST /api/v1/audit/purge/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuditPurge::test_purge_no_sudo` |
| `POST /api/v1/sudo/acquire/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSudoAcquire::test_sudo_acquire` |
| `GET /api/v1/sudo/status/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSudoStatus::test_sudo_status` |
| `DELETE /api/v1/sudo/release/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSudoRelease::test_sudo_release` |
| `GET /api/v1/users/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserList::test_user_list` |
| `POST /api/v1/users/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserList::test_user_create` |
| `GET /api/v1/users/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserDetail::test_user_detail` |
| `PATCH /api/v1/users/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserDetail::test_user_patch` |
| `POST /api/v1/users/{uuid}/disable/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserDisable::test_user_disable_no_sudo` |
| `POST /api/v1/users/{uuid}/enable/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserEnable::test_user_enable_already_active` |
| `GET /api/v1/workstations/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestWorkstationList::test_workstation_list` |
| `POST /api/v1/workstations/{int}/unblock/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestWorkstationUnblock::test_workstation_unblock_not_found` |
| `GET /api/v1/reports/subscriptions/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionListCreate::test_subscription_list` |
| `POST /api/v1/reports/subscriptions/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionListCreate::test_subscription_create` |
| `GET /api/v1/reports/subscriptions/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionDetail::test_subscription_detail` |
| `PATCH /api/v1/reports/subscriptions/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionDetail::test_subscription_patch` |
| `DELETE /api/v1/reports/subscriptions/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionDetail::test_subscription_delete_deactivate` |
| `POST /api/v1/reports/subscriptions/{uuid}/run-now/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionRunNow::test_run_now` |
| `GET /api/v1/reports/outbox/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOutboxList::test_outbox_list` |
| `GET /api/v1/reports/outbox/{uuid}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOutboxDetail::test_outbox_detail_not_found` |
| `GET /api/v1/reports/outbox/{uuid}/download/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOutboxDownload::test_outbox_download_not_found` |
| `POST /api/v1/reports/outbox/{uuid}/retry/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOutboxRetry::test_outbox_retry_not_found` |
| `POST /api/v1/reports/outbox/{uuid}/acknowledge/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestOutboxAcknowledge::test_outbox_acknowledge_not_found` |
| `GET /api/v1/reports/dashboard/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestReportDashboard::test_dashboard` |
| `POST /api/v1/logs/client-errors/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestClientErrorLog::test_client_error_log_authenticated` |
| `POST /api/v1/export/patients/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestExportPatients::test_export_patients_no_sudo` |
| `POST /api/v1/export/media/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestExportMedia::test_export_media_no_sudo` |
| `POST /api/v1/export/financials/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestExportFinancials::test_export_financials_no_sudo` |
| `GET /api/v1/policies/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPolicyList::test_policy_list` |
| `PATCH /api/v1/policies/{key}/` | yes | true no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPolicyUpdate::test_policy_update_no_sudo` |

## API Test Classification

### 1) True No-Mock HTTP

- `backend/tests/integration/test_api_blackbox.py` uses `django.test.Client` + `client.login(...)` and hits real URL routes end-to-end through middleware (`_make_client`, `Test*` methods).
- `backend/tests/integration/test_auth_api.py` is mostly true HTTP via `APIClient` + login endpoint session flow (e.g., `TestLogin::test_login_success`, `TestSession::test_session_info`).

### 2) HTTP with Mocking / Auth Override

Detected `force_authenticate(...)` (auth-layer bypass/override):
- `backend/tests/conftest.py`: fixtures `auth_client`, `frontdesk_client`, `clinician_client`, `compliance_client`
- `backend/tests/integration/test_export_api.py`: `admin_client`, `frontdesk_client`
- `backend/tests/integration/test_regression.py`: `admin_client`, `frontdesk_client`, `clinician_client`, `comp_client`
- `backend/tests/integration/test_consent_media_enforcement.py`: fixture `client`
- `backend/tests/integration/test_financial_task_audit.py`: fixture `patient_id`
- Any test consuming those fixtures in: `test_patient_api.py`, `test_consent_api.py`, `test_media_api.py`, `test_financials_api.py`, `test_reports_api.py`, `test_admin_api.py`, `test_authorization.py`, and one test in `test_auth_api.py` (`TestHealthCheck::test_health_check_admin_detailed` via `auth_client`)

### 3) Non-HTTP (Unit / Direct Invocation)

- Pure unit tests: `backend/tests/unit/test_domain_services.py`, `backend/tests/unit/test_encryption.py`, `backend/tests/unit/test_media_services.py`, `backend/tests/unit/test_audit_chain.py`, `backend/tests/unit/test_audit_archival.py`
- Direct internal function tests bypassing HTTP: `backend/tests/unit/test_client_log_redaction.py` imports private functions from `apps.audit.views_client_logs`
- Integration tests with direct task execution: `backend/tests/integration/test_financial_task_audit.py` (`auto_close_unpaid_orders`, `generate_daily_reconciliation`), `backend/tests/integration/test_regression.py` (`deliver_outbox_item`)

## Coverage Summary

- Total endpoints: **79**
- Endpoints with HTTP tests: **79**
- Endpoints with true no-mock HTTP tests: **79**
- HTTP coverage: **100.0%**
- True API coverage: **100.0%**

## Unit Test Summary

Test files:
- `backend/tests/unit/test_domain_services.py`
- `backend/tests/unit/test_encryption.py`
- `backend/tests/unit/test_media_services.py`
- `backend/tests/unit/test_audit_chain.py`
- `backend/tests/unit/test_audit_archival.py`
- `backend/tests/unit/test_client_log_redaction.py`

Modules covered (static evidence):
- Controllers/views (direct/private-level): `apps.audit.views_client_logs` via `_get_fns()` in `test_client_log_redaction.py`
- Services/domain: `domain.services.consent_service`, `domain.services.financial_service`, `apps.media_engine.services`, `apps.audit.service`, `infrastructure.encryption.service`
- Repositories/models (via ORM assertions): `apps.audit.models`, `apps.media_engine.models`, `apps.financials.models`
- Auth/guards/middleware (indirect through integration assertions): workstation header enforcement and role/sudo boundaries in `test_regression.py`, `test_authorization.py`, `test_admin_api.py`, `test_api_blackbox.py`

Important modules not directly unit-tested (by dedicated unit files):
- Middleware classes in `backend/infrastructure/middleware/*.py` (request-id, encryption context, session timeout, throttle, sudo, audit logging)
- Serializer modules across apps (`backend/apps/*/serializers.py`) lack explicit serializer-unit tests
- Permissions module `backend/apps/accounts/permissions.py` lacks direct unit tests (covered mainly via integration outcomes)

## API Observability Check

- Strong: black-box tests explicitly show method/path, payload, and response assertions (e.g., `test_api_blackbox.py` patient/media/financial flows).
- Medium weaknesses: several tests validate only status code on negative paths (e.g., outbox not-found tests and some role-denial checks), giving limited response-shape visibility.
- Overall observability rating: **Good (not perfect)**.

## Tests Check

- `run_tests.sh` is Docker-based (`docker compose run`, `docker compose up`, `docker compose exec`) and does not require local package-manager installs.
- Test orchestration includes backend, frontend, and e2e stages in one script.
- Static note: script contains runtime health polling and seeding steps (expected for integration/e2e) but still container-contained.

## Test Coverage Score (0-100)

**91/100**

## Score Rationale

- + Full endpoint-level HTTP coverage with explicit method+path tests.
- + Presence of a large true no-mock black-box suite (`test_api_blackbox.py`).
- + Broad role/authorization and failure-path assertions.
- + Fullstack e2e suite exists (`e2e/tests/*.spec.ts`) and is wired in `run_tests.sh`.
- - Significant parallel usage of `force_authenticate(...)` in many integration suites weakens realism for those suites.
- - Some tests are shallow status-only checks without deep response/side-effect assertions.
- - Middleware/serializer/permission modules are not strongly unit-isolated.

## Key Gaps

- Heavy use of auth override (`force_authenticate`) across many integration files reduces confidence in authentication/session middleware behavior in those suites.
- Direct invocation of internal/private functions and tasks bypasses HTTP boundaries in several tests.
- Missing dedicated unit tests for middleware and permissions logic.
- Not all negative-path tests assert response schema/content beyond status code.

## Confidence & Assumptions

- Confidence: **High** for endpoint inventory and endpoint-to-test mapping (all derived from static URL/view/test code).
- No runtime execution was performed; all findings are static.
- Method inventory assumes `@api_view([...])` in view functions is authoritative for allowed verbs.

**Test Coverage Verdict:** **PASS with quality caveats**

---

# README Audit

## Project Type Detection

- README top section does **not explicitly label** project type as `fullstack/backend/web/...`.
- Light repository inspection indicates **fullstack** (`backend/`, `frontend/`, `e2e/`, `docker-compose.yml`).

## Hard Gate Evaluation

- README location: **PASS** (`README.md` exists at repo root).
- Formatting/readability: **PASS** (clear headings, sections, command blocks).
- Startup instructions (backend/fullstack requires `docker-compose up`): **PASS** (`docker-compose up --build -d` present).
- Access method (URL/port): **PASS** (frontend `:3000`, backend `:8000`, health endpoint listed).
- Verification method: **PASS** (curl health check + browser login flow).
- Environment rules (no local runtime installs): **PASS** (Docker/Docker Compose workflow only).
- Demo credentials (auth present): **PASS** (all roles with username+password provided).

## Engineering Quality

- Tech stack clarity: strong and explicit.
- Architecture explanation: concise but sufficient for onboarding.
- Testing instructions: clear, centralized via `run_tests.sh`.
- Security/roles: role matrix provided with operational notes.
- Workflow completeness: startup, seed, verify, stop all included.
- Presentation quality: professional and actionable.

## High Priority Issues

- README does not explicitly declare project type (`fullstack`) at top, despite strict requirement.

## Medium Priority Issues

- Mixed command style (`docker-compose` and `docker compose`) may cause minor operator inconsistency.

## Low Priority Issues

- Verification section could include one explicit API business endpoint example beyond health (optional quality improvement).

## Hard Gate Failures

- **None**

## README Verdict

**PASS**

**README Audit Verdict:** **PASS**
