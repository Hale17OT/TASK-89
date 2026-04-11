import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { OrderCreatePage } from "../OrderCreatePage";

vi.mock("@/api/endpoints/financials", () => ({
  createOrder: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn(),
  },
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("OrderCreatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders line item form fields (description, quantity, unit price)", () => {
    renderWithProviders(<OrderCreatePage />, { user: adminUser });

    expect(screen.getByPlaceholderText("Description")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Qty")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Unit Price")).toBeInTheDocument();
  });

  it('has an "Add Item" button', () => {
    renderWithProviders(<OrderCreatePage />, { user: adminUser });

    expect(screen.getByRole("button", { name: /add item/i })).toBeInTheDocument();
  });

  it("renders total display", () => {
    renderWithProviders(<OrderCreatePage />, { user: adminUser });

    expect(screen.getByText("Total")).toBeInTheDocument();
    expect(screen.getByText("$0.00")).toBeInTheDocument();
  });
});
