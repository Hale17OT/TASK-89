import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { PatientCreatePage } from "../PatientCreatePage";

vi.mock("@/api/endpoints/patients", () => ({
  createPatient: vi.fn(),
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("PatientCreatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form with all required fields (MRN, first name, last name, DOB, gender)", () => {
    renderWithProviders(<PatientCreatePage />, { user: adminUser });

    expect(screen.getByPlaceholderText("Medical Record Number")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("First name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Last name")).toBeInTheDocument();
    expect(screen.getByText("Date of Birth")).toBeInTheDocument();
    expect(screen.getByText("Gender")).toBeInTheDocument();
  });

  it("shows validation errors for empty required fields on submit", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PatientCreatePage />, { user: adminUser });

    await user.click(screen.getByRole("button", { name: /create patient/i }));

    await waitFor(() => {
      expect(screen.getByText("MRN is required")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText("First name is required")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText("Last name is required")).toBeInTheDocument();
    });
  });

  it("has submit button with correct label", () => {
    renderWithProviders(<PatientCreatePage />, { user: adminUser });

    expect(screen.getByRole("button", { name: /create patient/i })).toBeInTheDocument();
  });
});
