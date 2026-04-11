import { describe, it, expect, vi } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { ProtectedRoute } from "../ProtectedRoute";

describe("ProtectedRoute", () => {
  it("renders children when user has an allowed role", () => {
    renderWithProviders(
      <ProtectedRoute allowedRoles={["admin"]}>
        <div>Protected Content</div>
      </ProtectedRoute>,
      { user: { id: "1", username: "admin", role: "admin", full_name: "Admin User" } }
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("renders ForbiddenPage when user role is not in allowedRoles", () => {
    renderWithProviders(
      <ProtectedRoute allowedRoles={["admin"]}>
        <div>Protected Content</div>
      </ProtectedRoute>,
      { user: { id: "2", username: "clinician", role: "clinician", full_name: "Clinician User" } }
    );

    expect(screen.getByText("403")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("renders ForbiddenPage when user is null", () => {
    renderWithProviders(
      <ProtectedRoute allowedRoles={["admin"]}>
        <div>Protected Content</div>
      </ProtectedRoute>,
      { user: null }
    );

    expect(screen.getByText("403")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it('allows any valid role when allowedRoles is "all"', () => {
    renderWithProviders(
      <ProtectedRoute allowedRoles="all">
        <div>Protected Content</div>
      </ProtectedRoute>,
      { user: { id: "3", username: "frontdesk", role: "front_desk", full_name: "Front Desk" } }
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });
});
