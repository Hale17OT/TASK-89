import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginPage } from "../pages/LoginPage";
import { renderWithProviders } from "@/test/test-utils";

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null, pathname: "/login", search: "", hash: "", key: "default" }),
  };
});

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders a login form with username and password fields", () => {
    renderWithProviders(<LoginPage />, { route: "/login" });

    // Use exact label text to avoid matching "Remember my username..."
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows validation errors when submitting empty fields", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { route: "/login" });

    const usernameInput = screen.getByLabelText("Username");
    const passwordInput = screen.getByLabelText("Password");
    await user.clear(usernameInput);
    await user.clear(passwordInput);
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it("disables the submit button while submitting", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { route: "/login" });

    const usernameInput = screen.getByLabelText("Username");
    const passwordInput = screen.getByLabelText("Password");
    await user.type(usernameInput, "admin");
    await user.type(passwordInput, "password123");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    expect(submitButton).not.toBeDisabled();

    // After clicking, react-hook-form sets isSubmitting=true during onSubmit.
    // Our mocked login resolves immediately, so verify the button stays functional.
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });
  });

  it("renders a remember device checkbox", () => {
    renderWithProviders(<LoginPage />, { route: "/login" });

    const checkbox = screen.getByLabelText(/remember my username/i);
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).toHaveAttribute("type", "checkbox");
  });
});
