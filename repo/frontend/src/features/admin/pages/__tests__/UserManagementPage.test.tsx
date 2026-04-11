import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithProviders, screen, waitFor } from "@/test/test-utils";
import UserManagementPage from "../UserManagementPage";

vi.mock("@/api/endpoints/admin", () => ({
  listUsers: vi.fn(),
  createUser: vi.fn(),
  disableUser: vi.fn(),
  enableUser: vi.fn(),
}));

import { listUsers } from "@/api/endpoints/admin";

const mockListUsers = vi.mocked(listUsers);

const adminUser = { id: "1", username: "admin", role: "admin", full_name: "Admin" };

describe("UserManagementPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Create User" button', () => {
    mockListUsers.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<UserManagementPage />, {
      user: adminUser,
      route: "/admin/users",
    });

    expect(screen.getByRole("button", { name: /create user/i })).toBeInTheDocument();
  });

  it("shows empty state when no users are returned", async () => {
    mockListUsers.mockResolvedValue({ results: [], count: 0, next: null, previous: null });
    renderWithProviders(<UserManagementPage />, {
      user: adminUser,
      route: "/admin/users",
    });

    await waitFor(() => {
      expect(screen.getByText(/no users found/i)).toBeInTheDocument();
    });
  });

  it("shows loading skeletons", () => {
    mockListUsers.mockReturnValue(new Promise(() => {}));
    renderWithProviders(<UserManagementPage />, {
      user: adminUser,
      route: "/admin/users",
    });

    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
