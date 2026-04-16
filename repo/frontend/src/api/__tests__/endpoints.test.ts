/**
 * API endpoint contract tests.
 *
 * These tests mock only the HTTP transport (apiClient) — NOT the endpoint
 * modules themselves — to verify every exported function sends the correct
 * HTTP method, URL, and payload.  This is fundamentally different from
 * component tests that mock the entire endpoint module.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock apiClient at the transport layer only
vi.mock("@/api/client", () => {
  const mock = {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: undefined }),
  };
  return { default: mock };
});

import apiClient from "@/api/client";

const mockGet = vi.mocked(apiClient.get);
const mockPost = vi.mocked(apiClient.post);
const mockPatch = vi.mocked(apiClient.patch);
const mockDelete = vi.mocked(apiClient.delete);

beforeEach(() => {
  vi.clearAllMocks();
});

// =========================================================================
// Auth endpoints
// =========================================================================
describe("auth endpoints", () => {
  it("login POSTs to auth/login/", async () => {
    const { login } = await import("@/api/endpoints/auth");
    mockPost.mockResolvedValueOnce({ data: { user: { id: "1" } } } as never);
    await login({ username: "admin", password: "pass" });
    expect(mockPost).toHaveBeenCalledWith("auth/login/", {
      username: "admin",
      password: "pass",
    });
  });

  it("logout POSTs to auth/logout/", async () => {
    const { logout } = await import("@/api/endpoints/auth");
    await logout();
    expect(mockPost).toHaveBeenCalledWith("auth/logout/");
  });

  it("getSession GETs auth/session/", async () => {
    const { getSession } = await import("@/api/endpoints/auth");
    await getSession();
    expect(mockGet).toHaveBeenCalledWith("auth/session/");
  });

  it("refreshSession POSTs to auth/session/refresh/", async () => {
    const { refreshSession } = await import("@/api/endpoints/auth");
    await refreshSession();
    expect(mockPost).toHaveBeenCalledWith("auth/session/refresh/");
  });

  it("changePassword POSTs to auth/change-password/", async () => {
    const { changePassword } = await import("@/api/endpoints/auth");
    const data = { current_password: "old", new_password: "new" };
    await changePassword(data);
    expect(mockPost).toHaveBeenCalledWith("auth/change-password/", data);
  });
});

// =========================================================================
// Patient endpoints
// =========================================================================
describe("patient endpoints", () => {
  it("searchPatients GETs patients/ with q param", async () => {
    const { searchPatients } = await import("@/api/endpoints/patients");
    mockGet.mockResolvedValueOnce({ data: [] } as never);
    await searchPatients("MRN-001");
    expect(mockGet).toHaveBeenCalledWith("patients/", { params: { q: "MRN-001" } });
  });

  it("createPatient POSTs to patients/create/", async () => {
    const { createPatient } = await import("@/api/endpoints/patients");
    const data = { mrn: "MRN-1", ssn: "123", first_name: "A", last_name: "B", date_of_birth: "2000-01-01", gender: "M" };
    await createPatient(data as never);
    expect(mockPost).toHaveBeenCalledWith("patients/create/", data);
  });

  it("getPatient GETs patients/{id}/", async () => {
    const { getPatient } = await import("@/api/endpoints/patients");
    await getPatient("abc-123");
    expect(mockGet).toHaveBeenCalledWith("patients/abc-123/");
  });

  it("updatePatient PATCHes patients/{id}/update/", async () => {
    const { updatePatient } = await import("@/api/endpoints/patients");
    await updatePatient("abc-123", { first_name: "New" } as never);
    expect(mockPatch).toHaveBeenCalledWith("patients/abc-123/update/", { first_name: "New" });
  });

  it("breakGlass POSTs to patients/{id}/break-glass/", async () => {
    const { breakGlass } = await import("@/api/endpoints/patients");
    const payload = { justification: "emergency", justification_category: "treatment" };
    await breakGlass("abc-123", payload as never);
    expect(mockPost).toHaveBeenCalledWith("patients/abc-123/break-glass/", payload);
  });
});

// =========================================================================
// Consent endpoints
// =========================================================================
describe("consent endpoints", () => {
  it("listConsents GETs patients/{patientId}/consents/", async () => {
    const { listConsents } = await import("@/api/endpoints/consents");
    await listConsents("p-1");
    expect(mockGet).toHaveBeenCalledWith("patients/p-1/consents/");
  });

  it("createConsent POSTs to patients/{patientId}/consents/", async () => {
    const { createConsent } = await import("@/api/endpoints/consents");
    const data = { effective_date: "2025-01-01", expiration_date: "2026-01-01" };
    await createConsent("p-1", data as never);
    expect(mockPost).toHaveBeenCalledWith("patients/p-1/consents/", data);
  });

  it("getConsent GETs patients/{patientId}/consents/{consentId}/", async () => {
    const { getConsent } = await import("@/api/endpoints/consents");
    await getConsent("p-1", "c-1");
    expect(mockGet).toHaveBeenCalledWith("patients/p-1/consents/c-1/");
  });

  it("revokeConsent POSTs to patients/{patientId}/consents/{consentId}/revoke/", async () => {
    const { revokeConsent } = await import("@/api/endpoints/consents");
    const data = { reason: "withdrawn" };
    await revokeConsent("p-1", "c-1", data as never);
    expect(mockPost).toHaveBeenCalledWith("patients/p-1/consents/c-1/revoke/", data);
  });
});

// =========================================================================
// Media endpoints
// =========================================================================
describe("media endpoints", () => {
  it("uploadMedia POSTs to media/upload/ with multipart header", async () => {
    const { uploadMedia } = await import("@/api/endpoints/media");
    const fd = new FormData();
    await uploadMedia(fd);
    expect(mockPost).toHaveBeenCalledWith("media/upload/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  });

  it("listMedia GETs media/ with params", async () => {
    const { listMedia } = await import("@/api/endpoints/media");
    await listMedia({ page: 2 });
    expect(mockGet).toHaveBeenCalledWith("media/", { params: { page: 2 } });
  });

  it("getMedia GETs media/{id}/", async () => {
    const { getMedia } = await import("@/api/endpoints/media");
    await getMedia("m-1");
    expect(mockGet).toHaveBeenCalledWith("media/m-1/");
  });

  it("downloadMedia GETs media/{id}/download/ as blob", async () => {
    const { downloadMedia } = await import("@/api/endpoints/media");
    await downloadMedia("m-1");
    expect(mockGet).toHaveBeenCalledWith("media/m-1/download/", {
      responseType: "blob",
    });
  });

  it("applyWatermark POSTs to media/{id}/watermark/", async () => {
    const { applyWatermark } = await import("@/api/endpoints/media");
    const config = { clinic_name: "Test", date_stamp: true, opacity: 0.5 };
    await applyWatermark("m-1", config);
    expect(mockPost).toHaveBeenCalledWith("media/m-1/watermark/", config);
  });

  it("authorizeRepost POSTs to media/{id}/repost/authorize/ with multipart", async () => {
    const { authorizeRepost } = await import("@/api/endpoints/media");
    const fd = new FormData();
    await authorizeRepost("m-1", fd);
    expect(mockPost).toHaveBeenCalledWith("media/m-1/repost/authorize/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  });

  it("attachMediaToPatient POSTs to media/{id}/attach-patient/", async () => {
    const { attachMediaToPatient } = await import("@/api/endpoints/media");
    await attachMediaToPatient("m-1", "p-1");
    expect(mockPost).toHaveBeenCalledWith("media/m-1/attach-patient/", {
      patient_id: "p-1",
    });
  });

  it("listInfringements GETs media/infringement/ with params", async () => {
    const { listInfringements } = await import("@/api/endpoints/media");
    await listInfringements({ status: "open" });
    expect(mockGet).toHaveBeenCalledWith("media/infringement/", {
      params: { status: "open" },
    });
  });

  it("createInfringement POSTs to media/infringement/ with multipart", async () => {
    const { createInfringement } = await import("@/api/endpoints/media");
    const fd = new FormData();
    await createInfringement(fd);
    expect(mockPost).toHaveBeenCalledWith("media/infringement/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  });

  it("getInfringement GETs media/infringement/{id}/", async () => {
    const { getInfringement } = await import("@/api/endpoints/media");
    await getInfringement("inf-1");
    expect(mockGet).toHaveBeenCalledWith("media/infringement/inf-1/");
  });

  it("updateInfringement PATCHes media/infringement/{id}/", async () => {
    const { updateInfringement } = await import("@/api/endpoints/media");
    await updateInfringement("inf-1", { status: "resolved" } as never);
    expect(mockPatch).toHaveBeenCalledWith("media/infringement/inf-1/", {
      status: "resolved",
    });
  });
});

// =========================================================================
// Financial endpoints
// =========================================================================
describe("financial endpoints", () => {
  it("listOrders GETs financials/orders/ with params", async () => {
    const { listOrders } = await import("@/api/endpoints/financials");
    await listOrders({ page: 1 });
    expect(mockGet).toHaveBeenCalledWith("financials/orders/", { params: { page: 1 } });
  });

  it("createOrder POSTs to financials/orders/", async () => {
    const { createOrder } = await import("@/api/endpoints/financials");
    const data = { patient_id: "p-1", line_items: [], notes: "" };
    await createOrder(data as never);
    expect(mockPost).toHaveBeenCalledWith("financials/orders/", data);
  });

  it("getOrder GETs financials/orders/{id}/", async () => {
    const { getOrder } = await import("@/api/endpoints/financials");
    await getOrder("ord-1");
    expect(mockGet).toHaveBeenCalledWith("financials/orders/ord-1/");
  });

  it("recordPayment POSTs to financials/orders/{id}/payments/ with idempotency key", async () => {
    const { recordPayment } = await import("@/api/endpoints/financials");
    const data = { amount: 100, method: "cash" };
    await recordPayment("ord-1", data, "idem-key-1");
    expect(mockPost).toHaveBeenCalledWith(
      "financials/orders/ord-1/payments/",
      data,
      { headers: { "Idempotency-Key": "idem-key-1" } }
    );
  });

  it("voidOrder POSTs to financials/orders/{id}/void/", async () => {
    const { voidOrder } = await import("@/api/endpoints/financials");
    await voidOrder("ord-1");
    expect(mockPost).toHaveBeenCalledWith("financials/orders/ord-1/void/");
  });

  it("listRefunds GETs financials/refunds/", async () => {
    const { listRefunds } = await import("@/api/endpoints/financials");
    await listRefunds();
    expect(mockGet).toHaveBeenCalledWith("financials/refunds/", { params: undefined });
  });

  it("createRefund POSTs to financials/orders/{id}/refunds/", async () => {
    const { createRefund } = await import("@/api/endpoints/financials");
    const data = { amount: 50, reason: "defective", original_payment_id: "pay-1" };
    await createRefund("ord-1", data);
    expect(mockPost).toHaveBeenCalledWith("financials/orders/ord-1/refunds/", data);
  });

  it("approveRefund POSTs to financials/refunds/{id}/approve/", async () => {
    const { approveRefund } = await import("@/api/endpoints/financials");
    await approveRefund("ref-1");
    expect(mockPost).toHaveBeenCalledWith("financials/refunds/ref-1/approve/");
  });

  it("processRefund POSTs to financials/refunds/{id}/process/", async () => {
    const { processRefund } = await import("@/api/endpoints/financials");
    await processRefund("ref-1");
    expect(mockPost).toHaveBeenCalledWith("financials/refunds/ref-1/process/");
  });

  it("listReconciliations GETs financials/reconciliation/", async () => {
    const { listReconciliations } = await import("@/api/endpoints/financials");
    await listReconciliations();
    expect(mockGet).toHaveBeenCalledWith("financials/reconciliation/", {
      params: undefined,
    });
  });

  it("getReconciliation GETs financials/reconciliation/{date}/", async () => {
    const { getReconciliation } = await import("@/api/endpoints/financials");
    await getReconciliation("2025-01-15");
    expect(mockGet).toHaveBeenCalledWith("financials/reconciliation/2025-01-15/");
  });

  it("downloadReconciliation GETs financials/reconciliation/{date}/download/ as blob", async () => {
    const { downloadReconciliation } = await import("@/api/endpoints/financials");
    await downloadReconciliation("2025-01-15", "csv");
    expect(mockGet).toHaveBeenCalledWith(
      "financials/reconciliation/2025-01-15/download/",
      { params: { format: "csv" }, responseType: "blob" }
    );
  });
});

// =========================================================================
// Admin endpoints
// =========================================================================
describe("admin endpoints", () => {
  it("listUsers GETs users/", async () => {
    const { listUsers } = await import("@/api/endpoints/admin");
    await listUsers({ role: "admin" });
    expect(mockGet).toHaveBeenCalledWith("users/", { params: { role: "admin" } });
  });

  it("createUser POSTs to users/", async () => {
    const { createUser } = await import("@/api/endpoints/admin");
    const data = { username: "new", password: "pass", role: "admin" };
    await createUser(data as never);
    expect(mockPost).toHaveBeenCalledWith("users/", data);
  });

  it("getUser GETs users/{id}/", async () => {
    const { getUser } = await import("@/api/endpoints/admin");
    await getUser("u-1");
    expect(mockGet).toHaveBeenCalledWith("users/u-1/");
  });

  it("updateUser PATCHes users/{id}/", async () => {
    const { updateUser } = await import("@/api/endpoints/admin");
    await updateUser("u-1", { full_name: "Updated" } as never);
    expect(mockPatch).toHaveBeenCalledWith("users/u-1/", { full_name: "Updated" });
  });

  it("disableUser POSTs to users/{id}/disable/", async () => {
    const { disableUser } = await import("@/api/endpoints/admin");
    await disableUser("u-1", { confirm: true });
    expect(mockPost).toHaveBeenCalledWith("users/u-1/disable/", { confirm: true });
  });

  it("enableUser POSTs to users/{id}/enable/", async () => {
    const { enableUser } = await import("@/api/endpoints/admin");
    await enableUser("u-1");
    expect(mockPost).toHaveBeenCalledWith("users/u-1/enable/");
  });

  it("listWorkstations GETs workstations/", async () => {
    const { listWorkstations } = await import("@/api/endpoints/admin");
    await listWorkstations();
    expect(mockGet).toHaveBeenCalledWith("workstations/", { params: undefined });
  });

  it("unblockWorkstation POSTs to workstations/{id}/unblock/", async () => {
    const { unblockWorkstation } = await import("@/api/endpoints/admin");
    await unblockWorkstation(42);
    expect(mockPost).toHaveBeenCalledWith("workstations/42/unblock/");
  });

  it("listAuditEntries GETs audit/entries/", async () => {
    const { listAuditEntries } = await import("@/api/endpoints/admin");
    await listAuditEntries();
    expect(mockGet).toHaveBeenCalledWith("audit/entries/", { params: undefined });
  });

  it("getAuditEntry GETs audit/entries/{id}/", async () => {
    const { getAuditEntry } = await import("@/api/endpoints/admin");
    await getAuditEntry(99);
    expect(mockGet).toHaveBeenCalledWith("audit/entries/99/");
  });

  it("verifyAuditChain POSTs to audit/verify-chain/", async () => {
    const { verifyAuditChain } = await import("@/api/endpoints/admin");
    await verifyAuditChain();
    expect(mockPost).toHaveBeenCalledWith("audit/verify-chain/");
  });

  it("purgeAudit POSTs to audit/purge/ with confirm", async () => {
    const { purgeAudit } = await import("@/api/endpoints/admin");
    await purgeAudit("2024-01-01");
    expect(mockPost).toHaveBeenCalledWith("audit/purge/", {
      before_date: "2024-01-01",
      confirm: true,
    });
  });

  it("acquireSudo POSTs to sudo/acquire/", async () => {
    const { acquireSudo } = await import("@/api/endpoints/admin");
    await acquireSudo("mypass", "user_disable");
    expect(mockPost).toHaveBeenCalledWith("sudo/acquire/", {
      password: "mypass",
      action_class: "user_disable",
    });
  });

  it("getSudoStatus GETs sudo/status/", async () => {
    const { getSudoStatus } = await import("@/api/endpoints/admin");
    await getSudoStatus();
    expect(mockGet).toHaveBeenCalledWith("sudo/status/");
  });

  it("releaseSudo DELETEs sudo/release/", async () => {
    const { releaseSudo } = await import("@/api/endpoints/admin");
    await releaseSudo();
    expect(mockDelete).toHaveBeenCalledWith("sudo/release/");
  });
});
