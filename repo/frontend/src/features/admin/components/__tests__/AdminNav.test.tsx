import { describe, it, expect } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { AdminNav } from "../AdminNav";

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("AdminNav", () => {
  it("renders all admin navigation links (Users, Throttling, Bulk Export, Audit Log, Policies)", () => {
    renderWithProviders(<AdminNav />, {
      user: adminUser,
      route: "/admin/users",
    });

    expect(screen.getByRole("link", { name: "Users" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Throttling" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Bulk Export" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Audit Log" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Policies" })).toBeInTheDocument();
  });

  it("active link has different styling", () => {
    renderWithProviders(<AdminNav />, {
      user: adminUser,
      route: "/admin/users",
    });

    const usersLink = screen.getByRole("link", { name: "Users" });
    const throttlingLink = screen.getByRole("link", { name: "Throttling" });

    // Active link should have bg-background (active style) while inactive has text-muted-foreground
    expect(usersLink.className).toContain("bg-background");
    expect(throttlingLink.className).toContain("text-muted-foreground");
  });
});
