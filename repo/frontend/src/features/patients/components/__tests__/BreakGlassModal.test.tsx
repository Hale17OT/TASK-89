import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { BreakGlassModal } from "../BreakGlassModal";

vi.mock("@/api/endpoints/patients", () => ({
  breakGlass: vi.fn(),
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

const defaultProps = {
  patientId: "p1",
  open: true,
  onClose: vi.fn(),
  onSuccess: vi.fn(),
};

describe("BreakGlassModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders justification textarea and category select", () => {
    renderWithProviders(<BreakGlassModal {...defaultProps} />, { user: adminUser });

    expect(screen.getByText("Justification Category")).toBeInTheDocument();
    expect(screen.getByText("Justification")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/describe why you need access/i)).toBeInTheDocument();
    expect(screen.getByText("Select a category")).toBeInTheDocument();
  });

  it("enforces minimum 20 character justification", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BreakGlassModal {...defaultProps} />, { user: adminUser });

    // Select a category
    const select = screen.getByRole("combobox");
    await user.selectOptions(select, "emergency");

    // Type a short justification
    const textarea = screen.getByPlaceholderText(/describe why you need access/i);
    await user.type(textarea, "too short");

    // Submit
    await user.click(screen.getByRole("button", { name: /confirm access/i }));

    await waitFor(() => {
      expect(screen.getByText(/justification must be at least 20 characters/i)).toBeInTheDocument();
    });
  });

  it("has a submit button present", () => {
    renderWithProviders(<BreakGlassModal {...defaultProps} />, { user: adminUser });

    expect(screen.getByRole("button", { name: /confirm access/i })).toBeInTheDocument();
  });
});
