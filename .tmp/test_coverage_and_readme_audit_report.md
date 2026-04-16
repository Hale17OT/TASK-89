# Test Coverage Audit

## Backend Endpoint Inventory

Resolved from root URL includes in `backend/medrights/urls.py` and app URL maps in:
- `backend/apps/health/urls.py`
- `backend/apps/accounts/urls.py`, `backend/apps/accounts/urls_sudo.py`, `backend/apps/accounts/urls_users.py`, `backend/apps/accounts/urls_workstations.py`, `backend/apps/accounts/urls_export.py`, `backend/apps/accounts/urls_policy.py`
- `backend/apps/mpi/urls.py`
- `backend/apps/consent/urls.py`
- `backend/apps/media_engine/urls.py`
- `backend/apps/financials/urls.py`
- `backend/apps/audit/urls.py`, `backend/apps/audit/urls_client_logs.py`
- `backend/apps/reports/urls.py`

Total unique endpoints (`METHOD + resolved PATH`): **79**

1. `GET /api/v1/health/`
2. `GET /api/v1/auth/csrf/`
3. `POST /api/v1/auth/login/`
4. `POST /api/v1/auth/logout/`
5. `GET /api/v1/auth/session/`
6. `POST /api/v1/auth/session/refresh/`
7. `POST /api/v1/auth/change-password/`
8. `POST /api/v1/auth/remember-device/`
9. `GET /api/v1/auth/remember-device/prefill/`
10. `GET /api/v1/auth/guest-profiles/`
11. `POST /api/v1/auth/guest-profiles/`
12. `POST /api/v1/auth/guest-profiles/:pk/activate/`
13. `GET /api/v1/auth/guest-profiles/:pk/recent-patients/`
14. `POST /api/v1/auth/guest-profiles/:pk/recent-patients/`
15. `GET /api/v1/patients/`
16. `POST /api/v1/patients/create/`
17. `GET /api/v1/patients/:pk/`
18. `PATCH /api/v1/patients/:pk/update/`
19. `POST /api/v1/patients/:pk/break-glass/`
20. `GET /api/v1/patients/:patient_id/consents/`
21. `POST /api/v1/patients/:patient_id/consents/`
22. `GET /api/v1/patients/:patient_id/consents/:pk/`
23. `POST /api/v1/patients/:patient_id/consents/:pk/revoke/`
24. `POST /api/v1/media/upload/`
25. `GET /api/v1/media/`
26. `GET /api/v1/media/:pk/`
27. `GET /api/v1/media/:pk/download/`
28. `POST /api/v1/media/:pk/watermark/`
29. `POST /api/v1/media/:pk/attach-patient/`
30. `POST /api/v1/media/:pk/repost/authorize/`
31. `GET /api/v1/media/infringement/`
32. `POST /api/v1/media/infringement/`
33. `GET /api/v1/media/infringement/:pk/`
34. `PATCH /api/v1/media/infringement/:pk/`
35. `GET /api/v1/financials/orders/`
36. `POST /api/v1/financials/orders/`
37. `GET /api/v1/financials/orders/:order_id/`
38. `POST /api/v1/financials/orders/:order_id/payments/`
39. `POST /api/v1/financials/orders/:order_id/void/`
40. `POST /api/v1/financials/orders/:order_id/refunds/`
41. `GET /api/v1/financials/refunds/`
42. `POST /api/v1/financials/refunds/:refund_id/approve/`
43. `POST /api/v1/financials/refunds/:refund_id/process/`
44. `GET /api/v1/financials/reconciliation/`
45. `GET /api/v1/financials/reconciliation/:date/`
46. `GET /api/v1/financials/reconciliation/:date/download/`
47. `GET /api/v1/audit/entries/`
48. `GET /api/v1/audit/entries/:pk/`
49. `POST /api/v1/audit/verify-chain/`
50. `POST /api/v1/audit/purge/`
51. `POST /api/v1/logs/client-errors/`
52. `GET /api/v1/reports/subscriptions/`
53. `POST /api/v1/reports/subscriptions/`
54. `GET /api/v1/reports/subscriptions/:pk/`
55. `PATCH /api/v1/reports/subscriptions/:pk/`
56. `DELETE /api/v1/reports/subscriptions/:pk/`
57. `POST /api/v1/reports/subscriptions/:pk/run-now/`
58. `GET /api/v1/reports/outbox/`
59. `GET /api/v1/reports/outbox/:pk/`
60. `GET /api/v1/reports/outbox/:pk/download/`
61. `POST /api/v1/reports/outbox/:pk/retry/`
62. `POST /api/v1/reports/outbox/:pk/acknowledge/`
63. `GET /api/v1/reports/dashboard/`
64. `POST /api/v1/sudo/acquire/`
65. `GET /api/v1/sudo/status/`
66. `DELETE /api/v1/sudo/release/`
67. `GET /api/v1/users/`
68. `POST /api/v1/users/`
69. `GET /api/v1/users/:pk/`
70. `PATCH /api/v1/users/:pk/`
71. `POST /api/v1/users/:pk/disable/`
72. `POST /api/v1/users/:pk/enable/`
73. `GET /api/v1/workstations/`
74. `POST /api/v1/workstations/:pk/unblock/`
75. `POST /api/v1/export/patients/`
76. `POST /api/v1/export/media/`
77. `POST /api/v1/export/financials/`
78. `GET /api/v1/policies/`
79. `PATCH /api/v1/policies/:key/`

## API Test Mapping Table

Legend: all mapped coverage below is HTTP-to-route-handler; no controller/service transport mocks were found in inspected backend tests.

| Endpoint | Covered | Test type | Test files | Evidence |
|---|---|---|---|---|
| `GET /api/v1/health/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/blackbox/test_bb_auth.py` | `TestHealthCheck.test_health_check_public_minimal`; `TestHealth.test_health_ok` |
| `GET /api/v1/auth/csrf/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestAuthCsrf.test_csrf_cookie` |
| `POST /api/v1/auth/login/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/blackbox/test_bb_auth.py` | `TestLogin.test_login_success`; `TestAuthLogin.test_login_success` |
| `POST /api/v1/auth/logout/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/blackbox/test_bb_auth.py` | `TestLogout.test_logout`; `TestAuthLogout.test_logout_authenticated` |
| `GET /api/v1/auth/session/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py` | `TestSession.test_session_info` |
| `POST /api/v1/auth/session/refresh/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_auth.py`, `backend/tests/integration/test_api_blackbox.py` | `TestAuthSession.test_session_refresh` |
| `POST /api/v1/auth/change-password/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py` | `TestChangePassword.test_change_password_success` |
| `POST /api/v1/auth/remember-device/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRememberDevice.test_remember_device_post` |
| `GET /api/v1/auth/remember-device/prefill/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRememberDevice.test_remember_device_prefill_no_cookie` |
| `GET /api/v1/auth/guest-profiles/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles.test_guest_profile_list` |
| `POST /api/v1/auth/guest-profiles/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles.test_guest_profile_create` |
| `POST /api/v1/auth/guest-profiles/:pk/activate/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles.test_guest_profile_activate` |
| `GET /api/v1/auth/guest-profiles/:pk/recent-patients/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles.test_guest_recent_patients_list` |
| `POST /api/v1/auth/guest-profiles/:pk/recent-patients/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestGuestProfiles.test_guest_recent_patients_post` |
| `GET /api/v1/patients/` | Yes | True no-mock HTTP | `backend/tests/integration/test_patient_api.py`, `backend/tests/integration/blackbox/test_bb_patients.py` | `TestPatientSearch.test_search_patient_by_mrn`; `TestPatientSearch.test_search_patients` |
| `POST /api/v1/patients/create/` | Yes | True no-mock HTTP | `backend/tests/integration/test_patient_api.py`, `backend/tests/integration/blackbox/test_bb_patients.py` | `TestPatientCreate.test_create_patient`; `TestPatientCreate.test_create_patient_admin` |
| `GET /api/v1/patients/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_patient_api.py` | `TestPatientDetail.test_patient_detail_masked` |
| `PATCH /api/v1/patients/:pk/update/` | Yes | True no-mock HTTP | `backend/tests/integration/test_patient_api.py` | `TestPatientUpdate.test_patient_update` |
| `POST /api/v1/patients/:pk/break-glass/` | Yes | True no-mock HTTP | `backend/tests/integration/test_patient_api.py` | `TestBreakGlass.test_break_glass_unmasks` |
| `GET /api/v1/patients/:patient_id/consents/` | Yes | True no-mock HTTP | `backend/tests/integration/test_consent_api.py` | `TestConsentList.test_list_consents` |
| `POST /api/v1/patients/:patient_id/consents/` | Yes | True no-mock HTTP | `backend/tests/integration/test_consent_api.py` | `TestConsentCreate.test_create_consent` |
| `GET /api/v1/patients/:patient_id/consents/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestConsentDetail.test_consent_detail` |
| `POST /api/v1/patients/:patient_id/consents/:pk/revoke/` | Yes | True no-mock HTTP | `backend/tests/integration/test_consent_api.py` | `TestConsentRevoke.test_revoke_consent` |
| `POST /api/v1/media/upload/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py`, `backend/tests/integration/blackbox/test_bb_media.py` | `TestMediaUpload.test_upload_media`; `TestMediaUpload.test_upload_success` |
| `GET /api/v1/media/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py` | `TestMediaList.test_list_media` |
| `GET /api/v1/media/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py` | `TestMediaDetail.test_media_detail` |
| `GET /api/v1/media/:pk/download/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py`, `backend/tests/integration/test_consent_media_enforcement.py` | `TestRepostDownloadBlocked.test_repost_download_blocked`; `TestDownloadConsentEnforcement.test_download_with_active_consent_succeeds` |
| `POST /api/v1/media/:pk/watermark/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py` | `TestWatermark.test_watermark` |
| `POST /api/v1/media/:pk/attach-patient/` | Yes | True no-mock HTTP | `backend/tests/integration/test_consent_media_enforcement.py`, `backend/tests/integration/blackbox/test_bb_media.py` | `TestAttachPatientConsentEnforcement.test_attach_with_active_consent_succeeds`; `TestMediaAttachPatient.test_attach_patient` |
| `POST /api/v1/media/:pk/repost/authorize/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRepostAuthorize.test_repost_authorize_success` |
| `GET /api/v1/media/infringement/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py`, `backend/tests/integration/blackbox/test_bb_media.py` | `TestInfringementCreateComplianceOnly.test_compliance_user_can_create`; `TestInfringementCreate.test_infringement_list` |
| `POST /api/v1/media/infringement/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py`, `backend/tests/integration/blackbox/test_bb_media.py` | `TestInfringementCreateComplianceOnly.test_compliance_user_can_create`; `TestInfringementCreate.test_infringement_create` |
| `GET /api/v1/media/infringement/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestInfringementDetail.test_infringement_detail` |
| `PATCH /api/v1/media/infringement/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_media_api.py`, `backend/tests/integration/test_api_blackbox.py` | `TestInfringementStateTransition.test_state_transition`; `TestInfringementDetail.test_infringement_patch` |
| `GET /api/v1/financials/orders/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_financials.py` | `TestOrderListCreate.test_order_list` |
| `POST /api/v1/financials/orders/` | Yes | True no-mock HTTP | `backend/tests/integration/test_financials_api.py` | `TestOrderCreate.test_create_order` |
| `GET /api/v1/financials/orders/:order_id/` | Yes | True no-mock HTTP | `backend/tests/integration/test_financials_api.py`, `backend/tests/integration/blackbox/test_bb_financials.py` | `TestPayments.test_record_payment_cash`; `TestOrderDetail.test_order_detail` |
| `POST /api/v1/financials/orders/:order_id/payments/` | Yes | True no-mock HTTP | `backend/tests/integration/test_financials_api.py` | `TestPayments.test_record_payment_cash` |
| `POST /api/v1/financials/orders/:order_id/void/` | Yes | True no-mock HTTP | `backend/tests/integration/test_financials_api.py` | `TestVoidOrder.test_void_order` |
| `POST /api/v1/financials/orders/:order_id/refunds/` | Yes | True no-mock HTTP | `backend/tests/integration/test_financials_api.py` | `TestRefunds.test_create_refund` |
| `GET /api/v1/financials/refunds/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRefundList.test_refund_list` |
| `POST /api/v1/financials/refunds/:refund_id/approve/` | Yes | True no-mock HTTP | `backend/tests/integration/test_financials_api.py`, `backend/tests/integration/test_api_blackbox.py` | `TestRefunds.test_approve_refund`; `TestRefundApprove.test_refund_approve` |
| `POST /api/v1/financials/refunds/:refund_id/process/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestRefundProcess.test_refund_process` |
| `GET /api/v1/financials/reconciliation/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestReconciliationList.test_reconciliation_list` |
| `GET /api/v1/financials/reconciliation/:date/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_financials.py`, `backend/tests/integration/test_api_blackbox.py` | `TestReconciliationDetail.test_reconciliation_detail_success`; `TestReconciliationDetail.test_reconciliation_detail_success` |
| `GET /api/v1/financials/reconciliation/:date/download/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestReconciliationDownload.test_reconciliation_download_success` |
| `GET /api/v1/audit/entries/` | Yes | True no-mock HTTP | `backend/tests/integration/test_admin_api.py`, `backend/tests/integration/test_api_blackbox.py` | `TestAuditListAdminOrCompliance.test_admin_can_access`; `TestAuditList.test_audit_list` |
| `GET /api/v1/audit/entries/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_admin.py` | `TestAuditDetail.test_audit_detail_success` |
| `POST /api/v1/audit/verify-chain/` | Yes | True no-mock HTTP | `backend/tests/integration/test_admin_api.py` | `TestAuditVerifyChain.test_admin_can_verify_chain` |
| `POST /api/v1/audit/purge/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_admin.py`, `backend/tests/integration/test_api_blackbox.py` | `TestAuditPurge.test_purge_success_with_sudo`; `TestAuditPurge.test_audit_purge_success` |
| `POST /api/v1/logs/client-errors/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py`, `backend/tests/unit/test_client_log_redaction.py` | `TestClientErrorLogs.test_client_error_log_authenticated`; `TestStrictMode.test_non_strict_allows_extra` |
| `GET /api/v1/reports/subscriptions/` | Yes | True no-mock HTTP | `backend/tests/integration/test_reports_api.py` | `TestListSubscriptions.test_compliance_can_list` |
| `POST /api/v1/reports/subscriptions/` | Yes | True no-mock HTTP | `backend/tests/integration/test_reports_api.py` | `TestCreateSubscription.test_admin_creates_subscription` |
| `GET /api/v1/reports/subscriptions/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py` | `TestSubscriptionDetail.test_subscription_detail` |
| `PATCH /api/v1/reports/subscriptions/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py`, `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionDetail.test_subscription_patch`; `TestSubscriptionDetail.test_subscription_patch` |
| `DELETE /api/v1/reports/subscriptions/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py` | `TestSubscriptionDetail.test_subscription_delete` |
| `POST /api/v1/reports/subscriptions/:pk/run-now/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSubscriptionRunNow.test_subscription_run_now` |
| `GET /api/v1/reports/outbox/` | Yes | True no-mock HTTP | `backend/tests/integration/test_reports_api.py`, `backend/tests/integration/test_api_blackbox.py` | `TestOutboxAccessControl.test_admin_can_access_outbox`; `TestOutboxList.test_outbox_list` |
| `GET /api/v1/reports/outbox/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py` | `TestOutboxDetail.test_outbox_detail_success` |
| `GET /api/v1/reports/outbox/:pk/download/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py` | `TestOutboxDownload.test_outbox_download_success` |
| `POST /api/v1/reports/outbox/:pk/retry/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py`, `backend/tests/integration/test_api_blackbox.py` | `TestOutboxRetry.test_outbox_retry_success`; `TestOutboxRetry.test_outbox_retry_success` |
| `POST /api/v1/reports/outbox/:pk/acknowledge/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_reports.py`, `backend/tests/integration/test_api_blackbox.py` | `TestOutboxAcknowledge.test_outbox_acknowledge_success`; `TestOutboxAcknowledge.test_outbox_acknowledge_success` |
| `GET /api/v1/reports/dashboard/` | Yes | True no-mock HTTP | `backend/tests/integration/test_reports_api.py` | `TestReportDashboard.test_admin_sees_dashboard` |
| `POST /api/v1/sudo/acquire/` | Yes | True no-mock HTTP | `backend/tests/integration/test_auth_api.py`, `backend/tests/integration/test_session_auth_middleware.py` | `TestSudoMode.test_sudo_acquire_success`; `TestSudoModeThroughSession.test_sudo_acquire_injects_into_session` |
| `GET /api/v1/sudo/status/` | Yes | True no-mock HTTP | `backend/tests/integration/test_session_auth_middleware.py`, `backend/tests/integration/test_api_blackbox.py` | `TestSudoModeThroughSession.test_sudo_status_reflects_acquired_token`; `TestSudoStatus.test_sudo_status` |
| `DELETE /api/v1/sudo/release/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestSudoRelease.test_sudo_release` |
| `GET /api/v1/users/` | Yes | True no-mock HTTP | `backend/tests/integration/test_admin_api.py`, `backend/tests/integration/blackbox/test_bb_admin.py` | `TestUserListAdminOnly.test_admin_can_list`; `TestUserList.test_user_list` |
| `POST /api/v1/users/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_admin.py`, `backend/tests/integration/test_api_blackbox.py` | `TestUserCreate.test_user_create`; `TestUserCreate.test_user_create` |
| `GET /api/v1/users/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserDetail.test_user_detail` |
| `PATCH /api/v1/users/:pk/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestUserDetail.test_user_patch` |
| `POST /api/v1/users/:pk/disable/` | Yes | True no-mock HTTP | `backend/tests/integration/test_admin_api.py`, `backend/tests/integration/test_session_auth_middleware.py`, `backend/tests/integration/blackbox/test_bb_admin.py` | `TestUserDisableRequiresSudo.test_disable_without_sudo_returns_403`; `TestSudoModeThroughSession.test_user_disable_succeeds_with_sudo`; `TestUserDisable.test_user_disable_success_with_sudo` |
| `POST /api/v1/users/:pk/enable/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_admin.py`, `backend/tests/integration/test_api_blackbox.py` | `TestUserEnable.test_user_enable_success`; `TestUserEnable.test_user_enable_success` |
| `GET /api/v1/workstations/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestWorkstationList.test_workstation_list` |
| `POST /api/v1/workstations/:pk/unblock/` | Yes | True no-mock HTTP | `backend/tests/integration/test_admin_api.py`, `backend/tests/integration/blackbox/test_bb_admin.py` | `TestWorkstationUnblockRequiresSudo.test_unblock_without_sudo_returns_403`; `TestWorkstationUnblock.test_workstation_unblock_success` |
| `POST /api/v1/export/patients/` | Yes | True no-mock HTTP | `backend/tests/integration/test_export_api.py`, `backend/tests/integration/test_regression.py` | `TestBulkExportPatients.test_export_patients_success_with_sudo`; `TestExportConsentScoping.test_patient_export_includes_with_correct_scope` |
| `POST /api/v1/export/media/` | Yes | True no-mock HTTP | `backend/tests/integration/test_export_api.py` | `TestBulkExportMedia.test_export_media_success_with_sudo` |
| `POST /api/v1/export/financials/` | Yes | True no-mock HTTP | `backend/tests/integration/test_export_api.py` | `TestBulkExportFinancials.test_export_financials_success_with_sudo` |
| `GET /api/v1/policies/` | Yes | True no-mock HTTP | `backend/tests/integration/test_api_blackbox.py` | `TestPolicyList.test_policy_list` |
| `PATCH /api/v1/policies/:key/` | Yes | True no-mock HTTP | `backend/tests/integration/blackbox/test_bb_admin.py`, `backend/tests/integration/test_api_blackbox.py` | `TestPolicyUpdate.test_policy_update_success_with_sudo`; `TestPolicyUpdate.test_policy_update_success_with_sudo` |

## API Test Classification

1. **True No-Mock HTTP**
   - `backend/tests/integration/test_api_blackbox.py`
   - `backend/tests/integration/blackbox/*.py`
   - `backend/tests/integration/test_auth_api.py`
   - `backend/tests/integration/test_patient_api.py`
   - `backend/tests/integration/test_consent_api.py`
   - `backend/tests/integration/test_media_api.py`
   - `backend/tests/integration/test_financials_api.py`
   - `backend/tests/integration/test_admin_api.py`
   - `backend/tests/integration/test_reports_api.py`
   - `backend/tests/integration/test_export_api.py`
   - `backend/tests/integration/test_authorization.py`
   - `backend/tests/integration/test_session_auth_middleware.py`
   - `backend/tests/integration/test_consent_media_enforcement.py`
   - HTTP cases inside `backend/tests/unit/test_client_log_redaction.py`

2. **HTTP with Mocking**
   - **None detected** in inspected backend tests.

3. **Non-HTTP (unit/integration without HTTP)**
   - `backend/tests/unit/test_encryption.py`
   - `backend/tests/unit/test_domain_services.py`
   - `backend/tests/unit/test_permissions.py`
   - `backend/tests/unit/test_middleware.py`
   - `backend/tests/unit/test_audit_chain.py`
   - `backend/tests/unit/test_audit_archival.py`
   - service-focused parts of `backend/tests/unit/test_media_services.py`
   - task/direct-call sections in `backend/tests/integration/test_financial_task_audit.py` and `backend/tests/integration/test_regression.py`

## Mock Detection

- `jest.mock`, `vi.mock`, `sinon.stub` patterns: **not applicable / not found** in Python test suite.
- Python mocking primitives (`unittest.mock`, `patch`, `monkeypatch`, `MagicMock`): **no mocking usage detected** in backend test files under `backend/tests/` (static grep over test sources).
- Explicit auth bypass (not mocking, but middleware-bypass risk):
  - `backend/tests/conftest.py` fixtures use `APIClient.force_authenticate` (`auth_client`, `frontdesk_client`, `clinician_client`, `compliance_client`).
  - `backend/tests/integration/test_export_api.py` fixtures use `force_authenticate` + `login`.
  - `backend/tests/integration/test_regression.py` fixtures use `force_authenticate`.
  - Compensation exists via real session-based black-box tests in `backend/tests/integration/blackbox/conftest.py` and `backend/tests/integration/test_session_auth_middleware.py`.

## Coverage Summary

- Total endpoints: **79**
- Endpoints with HTTP tests: **79**
- Endpoints with TRUE no-mock HTTP tests: **79**
- HTTP coverage: **100.0%**
- True API coverage: **100.0%**

## Unit Test Summary

Test files inspected:
- `backend/tests/unit/test_encryption.py`
- `backend/tests/unit/test_domain_services.py`
- `backend/tests/unit/test_permissions.py`
- `backend/tests/unit/test_middleware.py`
- `backend/tests/unit/test_media_services.py`
- `backend/tests/unit/test_audit_chain.py`
- `backend/tests/unit/test_audit_archival.py`
- `backend/tests/unit/test_client_log_redaction.py`

Modules covered:
- Controllers/views (indirectly via HTTP, plus strict-mode log endpoint in unit test)
- Services/domain:
  - `infrastructure.encryption.service`
  - `domain.services.consent_service`
  - `domain.services.financial_service`
  - `apps.media_engine.services`
  - `apps.audit.service`
- Middleware:
  - request id, sudo mode, session timeout, encryption context, audit logging
- Permissions/guards:
  - `apps.accounts.permissions.*`
- Repositories/data layer:
  - ORM model behavior is exercised, but repository-layer abstraction tests are not a distinct test layer

Important modules not clearly unit-tested (or only indirectly covered):
- `apps.accounts.tasks.py`
- `apps.consent.tasks.py`
- full negative-path matrix for `apps.reports.tasks` (only partial delivery-path tests in `backend/tests/integration/test_regression.py::TestDeliveryTargetRouting`)
- broad serializer-level unit tests across apps (most validation currently validated via integration requests)

## API Observability Check

Strong (clear endpoint + request input + response assertions):
- `backend/tests/integration/test_auth_api.py::TestLogin.test_login_success`
- `backend/tests/integration/test_patient_api.py::TestBreakGlass.test_break_glass_unmasks`
- `backend/tests/integration/test_financials_api.py::TestRefunds.test_create_refund`
- `backend/tests/integration/test_media_api.py::TestInfringementStateTransition.test_state_transition`

Weak or shallow in places (status-heavy assertions, limited payload semantics):
- several coarse-grained checks in `backend/tests/integration/test_api_blackbox.py` and `backend/tests/integration/blackbox/*.py` rely mainly on status codes and minimal key presence.

## Tests Check

`run_tests.sh` assessment (`run_tests.sh`):
- Docker-based orchestration: **Yes** (`docker compose run`, `docker compose up`)
- Local runtime dependency installs (`npm install`, `pip install`, `apt-get`): **Not present**
- Local host dependency for execution: **No hard dependency for DB/Redis/services**, backend and frontend tests use containerized commands.

## End-to-End Expectations (Fullstack)

- Fullstack E2E presence: **Yes**
  - E2E test suite exists under `e2e/tests/` with role/domain flows (`auth.spec.ts`, `patients.spec.ts`, `media-workflow.spec.ts`, `financials.spec.ts`, `reports.spec.ts`, etc.).
- Therefore missing FE↔BE testing is **not** a current gap.

## Test Quality & Sufficiency

- Strengths:
  - Endpoint-level HTTP coverage is complete.
  - Real session/middleware paths are explicitly tested (`backend/tests/integration/test_session_auth_middleware.py`).
  - Good auth/permission denial coverage across roles (`backend/tests/integration/test_authorization.py`).
  - Important domain correctness checks exist (consent validity, reconciliation, archival chain, redaction).
- Weaknesses:
  - Some broad black-box tests are assertion-light (status/key existence only).
  - Significant duplication between `test_api_blackbox.py` and `integration/blackbox/*`, increasing maintenance burden and drift risk.
  - Many integration suites use `force_authenticate`; middleware behavior can be bypassed unless mirrored by session-based tests.

## Test Coverage Score (0-100)

**88 / 100**

## Score Rationale

- +35: endpoint coverage (all 79 endpoints have HTTP hits)
- +20: true no-mock API path coverage present
- +15: robust auth/permissions and failure-path coverage
- +10: unit depth for middleware, encryption, audit chain, media services
- -7: duplicated black-box suites with shallow assertions in parts
- -5: frequent `force_authenticate` use in integration suites (middleware bypass risk, partially compensated)
- -0: no evidence of over-mocking

## Key Gaps

1. Duplicate black-box coverage (`test_api_blackbox.py` vs `integration/blackbox/*`) creates overhead without proportional assertion depth.
2. Several endpoint tests assert status only; deeper response-contract assertions are inconsistent.
3. Some non-HTTP critical modules (accounts/consent task layers) lack direct focused unit tests.

## Confidence & Assumptions

- Confidence: **High** for endpoint inventory and coverage classification.
- Assumptions:
  - Static review only; no runtime execution was performed.
  - Coverage determination is based strictly on visible test request calls and URL definitions.
  - DRF/Django test clients are treated as real HTTP-layer route execution in-process.

**Test Coverage Verdict: PASS (with quality caveats)**

# README Audit

Scope audited: `README.md` at repo root.

## Project Type Detection

- Declared type present at top: `README.md:3` -> `Project type: Fullstack`.
- Inferred type from repository structure also matches fullstack (`backend/`, `frontend/`, `e2e/`).

## Hard Gate Evaluation

1. **README location**
   - Required path `repo/README.md`: **PASS** (`README.md` exists).

2. **Formatting / readability**
   - Structured markdown with headings, lists, fenced blocks, table: **PASS**.

3. **Startup instructions (fullstack must include docker-compose up)**
   - Present: `docker-compose up --build -d` in `README.md:39`: **PASS**.

4. **Access method (URL + port)**
   - Frontend/API/health URLs provided in `README.md:55-57`: **PASS**.

5. **Verification method**
   - API verification via `curl` in `README.md:63` and UI flow check in `README.md:67`: **PASS**.

6. **Environment rules (no runtime installs / manual DB setup)**
   - No `npm install`, `pip install`, `apt-get`, manual DB setup instructions found in README: **PASS**.

7. **Demo credentials (auth exists -> all roles required)**
   - Provided for Admin/Front Desk/Clinician/Compliance with username+password in `README.md:96-101`: **PASS**.

## Engineering Quality

- Tech stack clarity: strong (`README.md:7-15`).
- Architecture explanation: adequate high-level narrative (`README.md:5`, `README.md:16-26`).
- Testing instructions: clear centralized runner (`README.md:74-90`, `run_tests.sh`).
- Security/roles documentation: present via seeded credentials and role notes (`README.md:96-101`).
- Workflow clarity: startup, seed, verify, stop flow is coherent (`README.md:34-72`).

## High Priority Issues

- None.

## Medium Priority Issues

- `README.md:50-52` includes a concrete admin password example in command invocation; acceptable for local/dev docs but should be explicitly labeled non-production in same step for stricter security posture.

## Low Priority Issues

- `README.md:81-82` (`chmod +x`) is Unix-centric and less useful on Windows hosts; optional OS-specific note could reduce friction.

## Hard Gate Failures

- None.

## README Verdict

**PASS**

---

Final Combined Verdicts:
- **Test Coverage Audit:** PASS (quality caveats; score 88/100)
- **README Audit:** PASS
