import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { PatientSearchPage } from "../PatientSearchPage";

vi.mock("@/api/endpoints/patients", () => ({
  searchPatients: vi.fn(),
}));

import { searchPatients } from "@/api/endpoints/patients";

const mockSearchPatients = vi.mocked(searchPatients);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("PatientSearchPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders search input and Create Patient button", () => {
    renderWithProviders(<PatientSearchPage />, { user: adminUser });

    expect(screen.getByPlaceholderText(/search by name, mrn/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create patient/i })).toBeInTheDocument();
  });

  it("shows empty state message when no search has been performed", () => {
    renderWithProviders(<PatientSearchPage />, { user: adminUser });

    expect(screen.getByText(/enter a search term above to find patients/i)).toBeInTheDocument();
  });

  it("shows loading skeletons while fetching", async () => {
    // Return a promise that never resolves to keep loading state
    mockSearchPatients.mockReturnValue(new Promise(() => {}));

    const user = userEvent.setup();
    renderWithProviders(<PatientSearchPage />, { user: adminUser });

    const input = screen.getByPlaceholderText(/search by name, mrn/i);
    await user.type(input, "John");

    await waitFor(() => {
      // The skeleton table renders column headers MRN, Name, DOB, Gender, Status
      const headers = screen.getAllByText("MRN");
      expect(headers.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("displays results table when data is returned", async () => {
    mockSearchPatients.mockResolvedValue([
      {
        id: "p1",
        mrn: "MRN001",
        name: "John Doe",
        date_of_birth: "1990-01-01",
        gender: "male",
        is_active: true,
      },
    ]);

    const user = userEvent.setup();
    renderWithProviders(<PatientSearchPage />, { user: adminUser });

    const input = screen.getByPlaceholderText(/search by name, mrn/i);
    await user.type(input, "John");

    await waitFor(() => {
      expect(screen.getByText("MRN001")).toBeInTheDocument();
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });
  });
});
