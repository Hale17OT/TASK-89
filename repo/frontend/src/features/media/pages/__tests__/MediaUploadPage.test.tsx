import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { MediaUploadPage } from "../MediaUploadPage";

vi.mock("@/api/endpoints/media", () => ({
  uploadMedia: vi.fn(),
  applyWatermark: vi.fn(),
}));

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("MediaUploadPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders file dropzone with correct accepted formats text ("JPEG, PNG")', () => {
    renderWithProviders(<MediaUploadPage />, { user: adminUser });

    expect(screen.getByText(/supported formats: jpeg, png/i)).toBeInTheDocument();
  });

  it("renders watermark controls (clinic name, date stamp, opacity slider)", () => {
    renderWithProviders(<MediaUploadPage />, { user: adminUser });

    expect(screen.getByText("Clinic Name")).toBeInTheDocument();
    expect(screen.getByText("Include date stamp")).toBeInTheDocument();
    expect(screen.getByText(/opacity/i)).toBeInTheDocument();
    expect(screen.getByRole("slider")).toBeInTheDocument();
  });

  it("opacity slider defaults to 35", () => {
    renderWithProviders(<MediaUploadPage />, { user: adminUser });

    const slider = screen.getByRole("slider");
    expect(slider).toHaveValue("35");
  });
});
