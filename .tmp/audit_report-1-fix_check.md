# Issue Recheck Results (Round 8, Static-Only)

Date: 2026-04-11

## Overall Outcome
- Fixed: 4
- Partially Fixed: 1
- Not Fixed: 0

## Issue-by-issue Status

1) **High** - Consent lifecycle not enforced for media usage/reuse  
**Status: Fixed**
- Evidence:
  - Consent validation present in upload/download/attach flows: `backend/apps/media_engine/serializers.py:130`, `backend/apps/media_engine/views.py:221`, `backend/apps/media_engine/views.py:552`
  - Required scope value enforcement present (`capture_storage`): `backend/apps/media_engine/serializers.py:136`, `backend/apps/media_engine/views.py:227`, `backend/apps/media_engine/views.py:558`

2) **High** - Financial auto-adjustments missing tamper-evident audit entries  
**Status: Fixed**
- Evidence:
  - Auto-close task now writes audit chain entries: `backend/apps/financials/tasks.py:50`
  - Reconciliation generation also writes audit chain entries: `backend/apps/financials/tasks.py:210`

3) **Medium** - Revocation UX not one-click  
**Status: Fixed**
- Evidence:
  - One-click handler implemented and used for revoke action: `frontend/src/features/patients/components/ConsentCard.tsx:50`, `frontend/src/features/patients/components/ConsentCard.tsx:56`, `frontend/src/features/patients/components/ConsentCard.tsx:112`

4) **Medium** - Client-error logging may ingest sensitive free-text  
**Status: Fixed**
- Evidence:
  - Deep redaction + URL redaction + extra sanitization present: `backend/apps/audit/views_client_logs.py:206`, `backend/apps/audit/views_client_logs.py:214`, `backend/apps/audit/views_client_logs.py:270`, `backend/apps/audit/views_client_logs.py:405`, `backend/apps/audit/views_client_logs.py:407`, `backend/apps/audit/views_client_logs.py:424`
- Residual risk:
  - Redaction remains heuristic; cannot statically prove complete prevention for all novel secret/PII formats.

5) **Low** - Inconsistent audit coverage on read-heavy/report endpoints  
**Status: Fixed**
- Evidence:
  - Media list endpoint emits audit context: `backend/apps/media_engine/views.py:101`, `backend/apps/media_engine/views.py:129`
  - Outbox list/detail endpoints emit audit context: `backend/apps/reports/views.py:218`, `backend/apps/reports/views.py:242`, `backend/apps/reports/views.py:260`, `backend/apps/reports/views.py:280`
