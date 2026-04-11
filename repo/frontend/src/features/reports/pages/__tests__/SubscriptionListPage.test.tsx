import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import { SubscriptionListPage } from "../SubscriptionListPage";

vi.mock("@/api/endpoints/reports", () => ({
  listSubscriptions: vi.fn(),
}));

import { listSubscriptions } from "@/api/endpoints/reports";

const mockListSubscriptions = vi.mocked(listSubscriptions);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("SubscriptionListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "New Subscription" and "View Outbox" buttons', () => {
    mockListSubscriptions.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<SubscriptionListPage />, { user: adminUser });

    expect(screen.getByRole("link", { name: /new subscription/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view outbox/i })).toBeInTheDocument();
  });

  it("shows empty state when no subscriptions are returned", async () => {
    mockListSubscriptions.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<SubscriptionListPage />, { user: adminUser });

    await waitFor(() => {
      expect(screen.getByText(/no subscriptions found/i)).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockListSubscriptions.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<SubscriptionListPage />, { user: adminUser });

    expect(screen.getByText(/loading subscriptions/i)).toBeInTheDocument();
  });
});
