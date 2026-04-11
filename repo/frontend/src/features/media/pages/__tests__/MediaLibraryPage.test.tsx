import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import { MediaLibraryPage } from "../MediaLibraryPage";

vi.mock("@/api/endpoints/media", () => ({
  listMedia: vi.fn(),
}));

import { listMedia } from "@/api/endpoints/media";

const mockListMedia = vi.mocked(listMedia);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("MediaLibraryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders upload button linking to /media/upload", () => {
    mockListMedia.mockResolvedValue({ results: [], count: 0 });
    renderWithProviders(<MediaLibraryPage />, { user: adminUser });

    const link = screen.getByRole("link", { name: /upload/i });
    expect(link).toHaveAttribute("href", "/media/upload");
  });

  it("shows empty state when no media is returned", async () => {
    mockListMedia.mockResolvedValue({ results: [], count: 0 });
    renderWithProviders(<MediaLibraryPage />, { user: adminUser });

    await waitFor(() => {
      expect(screen.getByText(/no media assets found/i)).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockListMedia.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<MediaLibraryPage />, { user: adminUser });

    // Loading state renders animated pulse skeleton cards
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
