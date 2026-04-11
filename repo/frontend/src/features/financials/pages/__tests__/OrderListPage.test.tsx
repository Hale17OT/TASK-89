import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import { OrderListPage } from "../OrderListPage";

vi.mock("@/api/endpoints/financials", () => ({
  listOrders: vi.fn(),
}));

import { listOrders } from "@/api/endpoints/financials";

const mockListOrders = vi.mocked(listOrders);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("OrderListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Create Order button", () => {
    mockListOrders.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<OrderListPage />, { user: adminUser });

    expect(screen.getByRole("link", { name: /create order/i })).toBeInTheDocument();
  });

  it("shows empty state when no orders are returned", async () => {
    mockListOrders.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<OrderListPage />, { user: adminUser });

    await waitFor(() => {
      expect(screen.getByText(/no orders found/i)).toBeInTheDocument();
    });
  });

  it("renders status filter dropdown", () => {
    mockListOrders.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<OrderListPage />, { user: adminUser });

    const select = screen.getByLabelText("Status:");
    expect(select).toBeInTheDocument();
    expect(select.tagName).toBe("SELECT");
  });
});
