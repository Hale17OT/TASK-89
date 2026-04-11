import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { ConsentCreateForm } from "../ConsentCreateForm";

vi.mock("@/api/endpoints/consents", () => ({
  createConsent: vi.fn(),
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

const defaultProps = {
  patientId: "p1",
  open: true,
  onClose: vi.fn(),
};

describe("ConsentCreateForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders purpose, effective date, and expiration date fields", () => {
    renderWithProviders(<ConsentCreateForm {...defaultProps} />, { user: adminUser });

    expect(screen.getByText("Purpose")).toBeInTheDocument();
    expect(screen.getByText("Effective Date")).toBeInTheDocument();
    expect(screen.getByText("Expiration Date")).toBeInTheDocument();
  });

  it("renders scope checkboxes", () => {
    renderWithProviders(<ConsentCreateForm {...defaultProps} />, { user: adminUser });

    expect(screen.getByText("Media Capture & Storage")).toBeInTheDocument();
    expect(screen.getByText("Internal Clinical Use")).toBeInTheDocument();
    expect(screen.getByText("Educational Use")).toBeInTheDocument();
    expect(screen.getByText("Marketing Use")).toBeInTheDocument();
    expect(screen.getByText("Research Use")).toBeInTheDocument();
    expect(screen.getByText("Data Sharing with Third Party")).toBeInTheDocument();
  });

  it("shows validation error when purpose is empty on submit", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConsentCreateForm {...defaultProps} />, { user: adminUser });

    await user.click(screen.getByRole("button", { name: /create consent/i }));

    await waitFor(() => {
      expect(screen.getByText("Purpose is required")).toBeInTheDocument();
    });
  });
});
