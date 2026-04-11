import { describe, it, expect } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { ForbiddenPage } from "../ForbiddenPage";

describe("ForbiddenPage", () => {
  it("renders a 403 heading", () => {
    renderWithProviders(<ForbiddenPage />);

    expect(screen.getByText("403")).toBeInTheDocument();
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });

  it("has a link to the dashboard", () => {
    renderWithProviders(<ForbiddenPage />);

    const link = screen.getByRole("link", { name: /back to dashboard/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/dashboard");
  });
});
