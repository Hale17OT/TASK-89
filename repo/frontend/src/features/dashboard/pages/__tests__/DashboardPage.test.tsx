import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import { DashboardPage } from "../DashboardPage";

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { count: 0 } }),
  },
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin User" };

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders welcome message with user's name", () => {
    renderWithProviders(<DashboardPage />, { user: adminUser });

    expect(screen.getByText(/welcome back, admin user/i)).toBeInTheDocument();
  });

  it("renders role-appropriate stat cards for admin", async () => {
    renderWithProviders(<DashboardPage />, { user: adminUser });

    // Admin should see Patients, Media Files, Open Infringements, Open Orders, Reports
    await waitFor(() => {
      expect(screen.getByText("Patients")).toBeInTheDocument();
      expect(screen.getByText("Media Files")).toBeInTheDocument();
      expect(screen.getByText("Open Orders")).toBeInTheDocument();
      expect(screen.getByText("Reports")).toBeInTheDocument();
    });
  });

  it("renders quick action links", () => {
    renderWithProviders(<DashboardPage />, { user: adminUser });

    expect(screen.getByText("Register Patient")).toBeInTheDocument();
    expect(screen.getByText("Upload Media")).toBeInTheDocument();
    expect(screen.getByText("View Reports")).toBeInTheDocument();
  });
});
