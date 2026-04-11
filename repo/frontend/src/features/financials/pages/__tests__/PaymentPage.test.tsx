import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { PaymentPage } from "../PaymentPage";

vi.mock("@/api/endpoints/financials", () => ({
  getOrder: vi.fn(),
  recordPayment: vi.fn(),
}));

import { getOrder } from "@/api/endpoints/financials";

const mockGetOrder = vi.mocked(getOrder);

// Mock useParams to provide orderId
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ orderId: "order-1" }),
  };
});

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

const mockOrder = {
  id: "order-1",
  order_number: "ORD-001",
  patient_id: "p1",
  status: "open",
  total_amount: "100.00",
  amount_paid: "0.00",
  created_at: "2024-01-01T00:00:00Z",
  line_items: [],
  payments: [],
  time_remaining_seconds: 1800,
};

describe("PaymentPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Cash and Check payment method options", async () => {
    mockGetOrder.mockResolvedValue(mockOrder as any);
    renderWithProviders(<PaymentPage />, { user: adminUser });

    await waitFor(() => {
      expect(screen.getByLabelText("Cash")).toBeInTheDocument();
      expect(screen.getByLabelText("Check")).toBeInTheDocument();
    });
  });

  it("shows check number field when Check is selected", async () => {
    mockGetOrder.mockResolvedValue(mockOrder as any);
    const user = userEvent.setup();
    renderWithProviders(<PaymentPage />, { user: adminUser });

    await waitFor(() => {
      expect(screen.getByLabelText("Cash")).toBeInTheDocument();
    });

    // Initially check number field should not be visible
    expect(screen.queryByLabelText("Check Number")).not.toBeInTheDocument();

    // Select Check payment method
    await user.click(screen.getByLabelText("Check"));

    await waitFor(() => {
      expect(screen.getByLabelText("Check Number")).toBeInTheDocument();
    });
  });
});
