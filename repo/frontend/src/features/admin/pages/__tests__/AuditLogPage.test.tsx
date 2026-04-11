import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import AuditLogPage from "../AuditLogPage";

vi.mock("@/api/endpoints/admin", () => ({
  listAuditEntries: vi.fn(),
  verifyAuditChain: vi.fn(),
}));

import { listAuditEntries } from "@/api/endpoints/admin";

const mockListAuditEntries = vi.mocked(listAuditEntries);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("AuditLogPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Verify Chain Integrity" button', () => {
    mockListAuditEntries.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<AuditLogPage />, {
      user: adminUser,
      route: "/admin/audit-log",
    });

    expect(screen.getByRole("button", { name: /verify chain integrity/i })).toBeInTheDocument();
  });

  it("renders filter inputs (event type, date range)", () => {
    mockListAuditEntries.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<AuditLogPage />, {
      user: adminUser,
      route: "/admin/audit-log",
    });

    // Event type select with "All Event Types" default
    expect(screen.getByDisplayValue("All Event Types")).toBeInTheDocument();

    // Date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBe(2);
  });
});
