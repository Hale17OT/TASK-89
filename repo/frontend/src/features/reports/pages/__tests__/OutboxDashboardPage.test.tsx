import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { OutboxDashboardPage } from "../OutboxDashboardPage";

vi.mock("@/api/endpoints/reports", () => ({
  getDashboard: vi.fn(),
  retryOutboxItem: vi.fn(),
  acknowledgeOutboxItem: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn(),
  },
}));

import { getDashboard } from "@/api/endpoints/reports";

const mockGetDashboard = vi.mocked(getDashboard);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("OutboxDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders report outbox heading", () => {
    mockGetDashboard.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<OutboxDashboardPage />, { user: adminUser });

    expect(screen.getByText("Report Outbox")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    mockGetDashboard.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<OutboxDashboardPage />, { user: adminUser });

    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });
});
