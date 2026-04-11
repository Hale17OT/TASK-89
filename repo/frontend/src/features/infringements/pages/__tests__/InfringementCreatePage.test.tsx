import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { InfringementCreatePage } from "../InfringementCreatePage";

vi.mock("@/api/endpoints/media", () => ({
  createInfringement: vi.fn(),
}));

vi.mock("html2canvas", () => ({
  default: vi.fn(),
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("InfringementCreatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders screenshot capture button", () => {
    renderWithProviders(<InfringementCreatePage />, { user: adminUser });

    expect(screen.getByRole("button", { name: /capture screenshot/i })).toBeInTheDocument();
  });

  it("renders reference field", () => {
    renderWithProviders(<InfringementCreatePage />, { user: adminUser });

    expect(
      screen.getByPlaceholderText(/url, file path, or document reference/i)
    ).toBeInTheDocument();
  });

  it("renders notes textarea with minimum length hint", () => {
    renderWithProviders(<InfringementCreatePage />, { user: adminUser });

    expect(
      screen.getByPlaceholderText(/describe the infringement in detail/i)
    ).toBeInTheDocument();
    expect(screen.getByText("0/50 min")).toBeInTheDocument();
  });
});
