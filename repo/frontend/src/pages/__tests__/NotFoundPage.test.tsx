import { describe, it, expect } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { NotFoundPage } from "../NotFoundPage";

describe("NotFoundPage", () => {
  it("renders a 404 heading", () => {
    renderWithProviders(<NotFoundPage />);

    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  it("has a link to the dashboard", () => {
    renderWithProviders(<NotFoundPage />);

    const link = screen.getByRole("link", { name: /back to dashboard/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/dashboard");
  });
});
