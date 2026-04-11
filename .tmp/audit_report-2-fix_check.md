# Issue Recheck Results (Static-Only, Follow-up)

Date: 2026-04-12

## Overall Outcome
- Fixed: 4
- Partially Fixed: 0
- Not Fixed: 0

## Issue-by-Issue Status

1) **High** - Frontend/backend contract mismatch breaks patient search during order creation  
**Status: Fixed**
- Evidence:
  - Order page now uses shared patient search API helper: `frontend/src/features/financials/pages/OrderCreatePage.tsx:92`
  - Shared helper calls backend with required `q` query param: `frontend/src/api/endpoints/patients.ts:16`
  - Backend search contract still expects `q` and returns list payload: `backend/apps/mpi/views.py:36`, `backend/apps/mpi/views.py:62`

2) **High** - Policy update endpoint lacks sudo/password re-auth guard  
**Status: Fixed**
- Evidence:
  - Policy update now requires sudo action `policy_update`: `backend/apps/accounts/views_policy.py:46`
  - Policy update now requires explicit confirmation: `backend/apps/accounts/views_policy.py:56`
  - `policy_update` action is now a valid sudo action class: `backend/apps/accounts/models.py:169`
  - Frontend policy update now sends `confirm: true`: `frontend/src/features/admin/pages/PolicyManagementPage.tsx:26`

3) **Medium** - UI role gating for "Attach to Patient" is stricter than backend policy  
**Status: Fixed**
- Evidence:
  - Frontend attach visibility now allows `front_desk`, `clinician`, and `admin`: `frontend/src/features/media/pages/MediaDetailPage.tsx:117`
  - Backend attach endpoint permission remains aligned with same roles: `backend/apps/media_engine/views.py:473`

4) **Low** - Infringement reporter display field is not backed by backend list serializer  
**Status: Fixed**
- Evidence:
  - Backend infringement list serializer now includes `reporter_name`: `backend/apps/media_engine/serializers.py:377`, `backend/apps/media_engine/serializers.py:384`
  - Frontend reporter field usage remains aligned: `frontend/src/features/infringements/pages/InfringementListPage.tsx:180`
