# MedRights Delivery Acceptance + Architecture Audit (Static-Only)

Date: 2026-04-12

## 1. Verdict
- Overall conclusion: **Partial Pass**
- Current implementation is broad and production-shaped, but there are still material requirement-fit gaps: a frontend/backend patient-search contract mismatch in order creation, and missing sudo/password re-auth on policy updates despite the prompt's second-confirmation requirement for sensitive admin actions.

## 2. Scope and Static Verification Boundary
- Reviewed code and docs only; no runtime execution was performed (`README.md:54`, `run_tests.sh:9`).
- Reviewed backend architecture/security paths across settings, middleware, permissions, views, serializers, and async tasks (`backend/medrights/settings/base.py:33`, `backend/medrights/settings/base.py:52`, `backend/apps/accounts/permissions.py:5`, `backend/apps/financials/tasks.py:17`).
- Reviewed frontend route guards, feature pages, and API endpoint clients (`frontend/src/router.tsx:59`, `frontend/src/features/financials/pages/OrderCreatePage.tsx:92`, `frontend/src/api/endpoints/patients.ts:11`).
- Reviewed representative backend/frontend tests for coverage mapping (`backend/tests/integration/test_consent_media_enforcement.py:209`, `backend/tests/integration/test_export_api.py:47`, `frontend/src/features/financials/pages/__tests__/OrderCreatePage.test.tsx:23`).
- Manual Verification Required: browser UX/responsiveness/accessibility, true runtime integration behavior (DB/Redis/Celery), and deployment characteristics.

## 3. Repository / Requirement Mapping Summary
- Core backend domains are present and wired: accounts/auth/sudo/workstations/export/policies, MPI, consent, media/infringement, financials, reports, audit, health (`backend/medrights/urls.py:5`, `backend/medrights/settings/base.py:42`).
- Security baseline is strong: Argon2-first password hashing, session timeout middleware, workstation throttling, sudo middleware, audit middleware (`backend/medrights/settings/base.py:112`, `backend/infrastructure/middleware/session_timeout.py:12`, `backend/medrights/settings/base.py:60`).
- Consent/media lifecycle checks are implemented on upload/download/attach, including effective/expiration/patient/scope validation (`backend/apps/media_engine/serializers.py:130`, `backend/apps/media_engine/views.py:221`, `backend/apps/media_engine/views.py:552`).
- Financial async processes now create tamper-evident audit entries for auto-close and reconciliation generation (`backend/apps/financials/tasks.py:50`, `backend/apps/financials/tasks.py:210`).

## 4. Section-by-section Review

### 1. Hard Gates
- **1.1 Documentation and static verifiability**
  - Conclusion: **Pass**
  - Evidence: setup/test instructions and architecture are present and consistent with code shape (`README.md:11`, `README.md:54`, `backend/medrights/settings/base.py:33`).
- **1.2 Material deviation from prompt**
  - Conclusion: **Partial Pass**
  - Evidence: policy updates are admin-only but do not enforce sudo/password re-auth (`backend/apps/accounts/views_policy.py:37`), while other high-impact admin actions do enforce sudo (`backend/apps/accounts/views_users.py:143`, `backend/apps/accounts/views_export.py:30`).

### 2. Delivery Completeness
- **2.1 Core explicit requirements coverage**
  - Conclusion: **Pass**
  - Evidence: required modules and major workflows exist across MPI/consent/media/infringements/financials/reports/audit (`backend/apps/mpi/views.py:27`, `backend/apps/consent/views.py:39`, `backend/apps/media_engine/views.py:590`, `backend/apps/financials/views.py:67`, `backend/apps/reports/views.py:30`, `backend/apps/audit/service.py:28`).
- **2.2 End-to-end 0->1 deliverable vs partial demo**
  - Conclusion: **Pass**
  - Evidence: full backend/frontend/test project with operational components and scheduled tasks (`backend/medrights/celery.py:12`, `backend/apps/reports/tasks.py:565`, `frontend/src/router.tsx:33`).

### 3. Engineering and Architecture Quality
- **3.1 Structure and module decomposition**
  - Conclusion: **Pass**
  - Evidence: app-level decomposition, middleware layering, and service boundaries are coherent (`backend/medrights/settings/base.py:33`, `backend/medrights/settings/base.py:52`, `backend/domain/services/patient_service.py:1`).
- **3.2 Maintainability/extensibility**
  - Conclusion: **Partial Pass**
  - Evidence: architecture is maintainable overall, but API contract divergence exists across frontend call sites (`frontend/src/features/financials/pages/OrderCreatePage.tsx:93`) vs shared endpoint wrapper and backend contract (`frontend/src/api/endpoints/patients.ts:16`, `backend/apps/mpi/views.py:36`).

### 4. Engineering Details and Professionalism
- **4.1 Error handling, logging, validation, API design**
  - Conclusion: **Partial Pass**
  - Evidence: strong validation and logging hygiene exist (`backend/infrastructure/exceptions.py:11`, `backend/apps/audit/views_client_logs.py:317`, `backend/medrights/settings/base.py:247`), but one frontend path uses an inconsistent patient search query param and response expectation (`frontend/src/features/financials/pages/OrderCreatePage.tsx:93`, `frontend/src/features/financials/pages/OrderCreatePage.tsx:95`, `backend/apps/mpi/views.py:62`).
- **4.2 Real product/service shape vs demo**
  - Conclusion: **Pass**
  - Evidence: includes background jobs, retention/audit, throttling, and export/reports lifecycle behavior (`backend/apps/financials/tasks.py:17`, `backend/apps/audit/tasks.py:54`, `backend/apps/reports/tasks.py:471`).

### 5. Prompt Understanding and Requirement Fit
- **5.1 Business goal/constraints fit**
  - Conclusion: **Partial Pass**
  - Evidence: permission design and consent controls strongly align overall, but policy-management path appears to miss the same re-auth/second-confirm semantics used elsewhere for sensitive admin operations (`backend/apps/accounts/views_policy.py:37`, `backend/apps/accounts/views_users.py:143`, `backend/apps/accounts/views_export.py:30`).

### 6. Aesthetics (frontend)
- **6.1 Visual/interaction quality**
  - Conclusion: **Cannot Confirm Statistically**
  - Evidence: UI components/routes exist, but rendered quality and responsive behavior require browser runtime checks (`frontend/src/router.tsx:69`, `frontend/src/features/media/pages/MediaDetailPage.tsx:177`, `frontend/src/features/infringements/pages/InfringementListPage.tsx:45`).

## 5. Issues / Suggestions (Severity-Rated)

- **Severity: High**
  - Title: Frontend/backend contract mismatch breaks patient search during order creation
  - Conclusion: **Fail**
  - Evidence: order page sends `search` and expects paginated results (`frontend/src/features/financials/pages/OrderCreatePage.tsx:93`, `frontend/src/features/financials/pages/OrderCreatePage.tsx:95`), while backend requires `q` and returns a plain list (`backend/apps/mpi/views.py:36`, `backend/apps/mpi/views.py:62`).
  - Impact: Patient lookup can fail or silently degrade in a critical billing workflow.
  - Minimum actionable fix: route order page through shared `searchPatients(q)` endpoint client (`frontend/src/api/endpoints/patients.ts:11`) and standardize response handling.

- **Severity: High**
  - Title: Policy update endpoint lacks sudo/password re-auth guard
  - Conclusion: **Fail**
  - Evidence: policy update is only `IsAdmin` (`backend/apps/accounts/views_policy.py:38`) with no sudo action check; sensitive peers enforce sudo (`backend/apps/accounts/views_users.py:143`, `backend/apps/accounts/views_export.py:30`).
  - Impact: Weakens defense-in-depth for high-impact administrative configuration changes.
  - Minimum actionable fix: require a sudo action class (for example `policy_update`) and explicit confirm semantics, consistent with other sensitive admin actions.

- **Severity: Medium**
  - Title: UI role gating for "Attach to Patient" is stricter than backend policy
  - Conclusion: **Partial Fail**
  - Evidence: backend permits front_desk/clinician/admin attach (`backend/apps/media_engine/views.py:473`), but UI shows action only for clinician (`frontend/src/features/media/pages/MediaDetailPage.tsx:117`, `frontend/src/features/media/pages/MediaDetailPage.tsx:299`), while route itself allows front_desk/clinician/admin (`frontend/src/router.tsx:71`).
  - Impact: Feature inconsistency for front-desk users and avoidable workflow friction.
  - Minimum actionable fix: align UI gating to backend policy or document intentional restriction and enforce it server-side too.

- **Severity: Low**
  - Title: Infringement reporter display field is not backed by backend list serializer
  - Conclusion: **Partial Fail**
  - Evidence: frontend expects optional `reporter_name` (`frontend/src/api/types/media.types.ts:45`, `frontend/src/features/infringements/pages/InfringementListPage.tsx:180`), but list serializer does not return it (`backend/apps/media_engine/serializers.py:380`).
  - Impact: Reporter column can collapse to fallback values, reducing clarity for investigations.
  - Minimum actionable fix: either add reporter display field in list/detail serializers or remove it from UI/types.

## 6. Security Review Summary
- **Authentication entry points**: **Pass** - login/logout/session/change-password/remember-device endpoints are defined and session controls are present (`backend/apps/accounts/urls.py:8`, `backend/apps/accounts/urls.py:12`, `backend/infrastructure/middleware/session_timeout.py:29`).
- **Route-level authorization**: **Pass** - custom role permissions are broadly applied in DRF endpoints (`backend/apps/accounts/permissions.py:44`, `backend/apps/media_engine/views.py:191`, `backend/apps/reports/views.py:31`).
- **Object-level authorization**: **Partial Pass** - strong consent-object validation in media flows (`backend/apps/media_engine/views.py:221`, `backend/apps/media_engine/views.py:552`), but frontend contract issues can still block intended object-selection flow in financial order creation (`frontend/src/features/financials/pages/OrderCreatePage.tsx:93`).
- **Function-level authorization**: **Partial Pass** - many dangerous admin functions enforce sudo (`backend/apps/accounts/views_users.py:143`, `backend/apps/accounts/views_workstations.py:40`, `backend/apps/accounts/views_export.py:30`), but policy update lacks equivalent re-auth (`backend/apps/accounts/views_policy.py:38`).
- **Tenant/data isolation**: **Pass (single-tenant model)** - architecture explicitly declares single-clinic/single-tenant-by-deployment with RBAC (`backend/medrights/settings/base.py:13`).
- **Admin/internal/debug protection**: **Partial Pass** - health endpoint is public but details are admin-only (`backend/apps/health/views.py:14`, `backend/apps/health/views.py:91`); public client-log endpoint is intentionally open with origin+throttle+sanitization (`backend/apps/audit/views_client_logs.py:317`, `backend/apps/audit/views_client_logs.py:361`).

## 7. Tests and Logging Review
- **Unit/integration breadth**: backend has substantial coverage for auth/authorization/consent/media/financials/reports/export and domain/security units (`backend/tests/integration/test_authorization.py:22`, `backend/tests/integration/test_consent_media_enforcement.py:209`, `backend/tests/unit/test_audit_chain.py:13`, `backend/tests/unit/test_client_log_redaction.py:1`).
- **Logging design**: structured JSON logging and audit-chain service are in place (`backend/medrights/settings/base.py:247`, `backend/apps/audit/service.py:126`).
- **Security-sensitive log ingestion**: client error endpoint has layered redaction and strict field controls; residual heuristic risk remains by design (`backend/apps/audit/views_client_logs.py:217`, `backend/apps/audit/views_client_logs.py:396`, `backend/apps/audit/views_client_logs.py:478`).
- **Coverage gaps identified statically**: no backend tests found for policy-management sudo/confirm behavior (`backend/tests/integration/test_admin_api.py:15`, `backend/tests/integration/test_export_api.py:47` vs no `/api/v1/policies/` tests), and order-create frontend tests do not validate search API contract (`frontend/src/features/financials/pages/__tests__/OrderCreatePage.test.tsx:23`).

## 8. Test Coverage Assessment (Static Audit)

### 8.1 Test Overview
- Backend: `pytest` integration + unit suites exist and are non-trivial (`backend/pytest.ini:1`, `backend/tests/integration/test_auth_api.py:1`, `backend/tests/unit/test_encryption.py:1`).
- Frontend: Vitest/component coverage exists across major domains (`frontend/package.json:10`, `frontend/src/features/financials/pages/__tests__/OrderCreatePage.test.tsx:1`).
- E2E: Playwright config exists but runtime validation was intentionally not performed (`e2e/playwright.config.ts:3`).

### 8.2 Coverage Mapping Table

| Requirement / Risk Point | Mapped Test Case(s) | Key Assertion | Coverage Assessment | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| Consent validation for media upload/download/attach | `backend/tests/integration/test_consent_media_enforcement.py:209` | Rejects revoked/expired/future/wrong-patient/wrong-scope | sufficient | None major in this area | Add edge-case around null/empty scope arrays in consent object |
| Sudo for dangerous admin actions | `backend/tests/integration/test_admin_api.py:15`, `backend/tests/integration/test_export_api.py:47` | 403 without sudo for disable/unblock/export | basically covered | No policy endpoint sudo tests | Add `/api/v1/policies/{key}/` tests for sudo-required + confirm behavior |
| Financial async audit trail | `backend/tests/integration/test_financial_task_audit.py:1` | Task-triggered financial events audited | basically covered | Audit payload quality assertions could be deeper | Add assertions on exact event_type/field_changes schema |
| Patient search API contract in order creation | `frontend/src/features/financials/pages/__tests__/OrderCreatePage.test.tsx:23` | Current tests only render controls | insufficient | No assertion on `q` param contract/result parsing | Add test mocking `apiClient.get` to assert `params: { q }` and list handling |
| UI permissions vs backend attach policy | (no direct test found) | N/A | insufficient | No UI role-gating contract test | Add test matrix for front_desk/clinician/admin visibility on Attach button |
| Infringement reporter display integrity | (no direct test found) | N/A | insufficient | No serialization/UI field-contract test | Add API contract test ensuring list/detail exposes reporter display field or UI omits it |

### 8.3 Security Coverage Audit
- **Authentication**: basically covered (`backend/tests/integration/test_auth_api.py:30`).
- **Route authorization**: sufficient (`backend/tests/integration/test_authorization.py:22`).
- **Object-level authorization**: sufficient in media/consent flows (`backend/tests/integration/test_consent_media_enforcement.py:209`).
- **Tenant/data isolation**: acceptable for declared single-tenant model (`backend/medrights/settings/base.py:13`).
- **Function-level auth for all sensitive admin operations**: insufficient (policy path gap is not tested and not enforced) (`backend/apps/accounts/views_policy.py:38`).

### 8.4 Final Coverage Judgment
- **Partial Pass**
- High-risk security controls are broadly tested, but the policy-management re-auth gap and frontend API-contract/UI-permission mismatches can slip through current coverage.

## 9. Final Notes
- This report is strictly static and evidence-based; no runtime claims are made.
- The project is close to acceptance quality, but the two High findings should be addressed before final sign-off.
