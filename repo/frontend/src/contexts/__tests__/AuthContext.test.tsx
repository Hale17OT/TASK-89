/**
 * Unit tests for AuthContext: authReducer state transitions and
 * AuthProvider / useAuth hook behaviour.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "../AuthContext";

// Mock the auth API at the transport level
vi.mock("@/api/endpoints/auth", () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getSession: vi.fn(),
  refreshSession: vi.fn(),
  changePassword: vi.fn(),
}));

// Mock useIdleTimer to avoid timer side-effects in tests
vi.mock("@/hooks/useIdleTimer", () => ({
  useIdleTimer: vi.fn(),
}));

import * as authApi from "@/api/endpoints/auth";

const mockLogin = vi.mocked(authApi.login);
const mockLogout = vi.mocked(authApi.logout);
const mockGetSession = vi.mocked(authApi.getSession);

// ---------------------------------------------------------------------------
// Test helper: renders a consumer that exposes AuthContext values
// ---------------------------------------------------------------------------

function TestConsumer() {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="user">{auth.user ? auth.user.username : "null"}</span>
      <span data-testid="loading">{String(auth.isLoading)}</span>
      <span data-testid="idle-warning">{String(auth.idleWarningVisible)}</span>
      <span data-testid="reauth">{String(auth.reauthRequired)}</span>
      <button
        data-testid="login-btn"
        onClick={() => auth.login({ username: "admin", password: "pass" })}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={() => auth.logout()}>
        Logout
      </button>
      <button
        data-testid="dispatch-idle-warning"
        onClick={() => auth.dispatch({ type: "IDLE_WARNING" })}
      >
        Idle Warning
      </button>
      <button
        data-testid="dispatch-idle-extend"
        onClick={() => auth.dispatch({ type: "IDLE_EXTEND" })}
      >
        Idle Extend
      </button>
      <button
        data-testid="dispatch-idle-expire"
        onClick={() => auth.dispatch({ type: "IDLE_EXPIRE" })}
      >
        Idle Expire
      </button>
      <button
        data-testid="dispatch-reauth"
        onClick={() =>
          auth.dispatch({
            type: "REAUTH_SUCCESS",
            payload: { id: "2", username: "reauthed", role: "admin", full_name: "R" } as never,
          })
        }
      >
        Reauth
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: no existing session
    mockGetSession.mockRejectedValue(new Error("no session"));
  });

  describe("initial session check", () => {
    it("shows loading initially, then resolves to no user when session fails", async () => {
      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("null");
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });
    });

    it("restores user from existing session", async () => {
      mockGetSession.mockResolvedValueOnce({
        user: { id: "1", username: "admin", role: "admin", full_name: "Admin" },
      } as never);

      renderWithProvider();

      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("admin");
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });
    });
  });

  describe("login", () => {
    it("sets user on successful login", async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValueOnce({
        user: { id: "1", username: "admin", role: "admin", full_name: "Admin" },
      } as never);

      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      await user.click(screen.getByTestId("login-btn"));

      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("admin");
      });
      expect(mockLogin).toHaveBeenCalledWith({
        username: "admin",
        password: "pass",
      });
    });

    it("clears loading on login failure", async () => {
      const user = userEvent.setup();
      mockLogin.mockRejectedValueOnce(new Error("bad credentials"));

      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      await expect(async () => {
        await user.click(screen.getByTestId("login-btn"));
      }).rejects.toThrow();

      // Should still be logged out
      expect(screen.getByTestId("user").textContent).toBe("null");
    });
  });

  describe("logout", () => {
    it("clears user on logout", async () => {
      const user = userEvent.setup();
      mockGetSession.mockResolvedValueOnce({
        user: { id: "1", username: "admin", role: "admin", full_name: "A" },
      } as never);
      mockLogout.mockResolvedValueOnce(undefined);

      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("admin");
      });

      await user.click(screen.getByTestId("logout-btn"));

      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("null");
      });
    });

    it("clears user even if API logout fails", async () => {
      const user = userEvent.setup();
      mockGetSession.mockResolvedValueOnce({
        user: { id: "1", username: "admin", role: "admin", full_name: "A" },
      } as never);
      mockLogout.mockRejectedValueOnce(new Error("network error"));

      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("admin");
      });

      await user.click(screen.getByTestId("logout-btn"));

      await waitFor(() => {
        expect(screen.getByTestId("user").textContent).toBe("null");
      });
    });
  });

  describe("idle state transitions", () => {
    it("IDLE_WARNING sets idleWarningVisible", async () => {
      const user = userEvent.setup();
      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      await user.click(screen.getByTestId("dispatch-idle-warning"));
      expect(screen.getByTestId("idle-warning").textContent).toBe("true");
    });

    it("IDLE_EXTEND clears idleWarningVisible", async () => {
      const user = userEvent.setup();
      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      await user.click(screen.getByTestId("dispatch-idle-warning"));
      expect(screen.getByTestId("idle-warning").textContent).toBe("true");

      await user.click(screen.getByTestId("dispatch-idle-extend"));
      expect(screen.getByTestId("idle-warning").textContent).toBe("false");
    });

    it("IDLE_EXPIRE sets reauthRequired and clears warning", async () => {
      const user = userEvent.setup();
      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      await user.click(screen.getByTestId("dispatch-idle-expire"));
      expect(screen.getByTestId("reauth").textContent).toBe("true");
      expect(screen.getByTestId("idle-warning").textContent).toBe("false");
    });

    it("REAUTH_SUCCESS clears reauthRequired and sets user", async () => {
      const user = userEvent.setup();
      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      await user.click(screen.getByTestId("dispatch-idle-expire"));
      expect(screen.getByTestId("reauth").textContent).toBe("true");

      await user.click(screen.getByTestId("dispatch-reauth"));
      expect(screen.getByTestId("reauth").textContent).toBe("false");
      expect(screen.getByTestId("user").textContent).toBe("reauthed");
    });
  });

  describe("session-expired event", () => {
    it("dispatches IDLE_EXPIRE on auth:session-expired event", async () => {
      renderWithProvider();
      await waitFor(() => {
        expect(screen.getByTestId("loading").textContent).toBe("false");
      });

      act(() => {
        window.dispatchEvent(new CustomEvent("auth:session-expired"));
      });

      expect(screen.getByTestId("reauth").textContent).toBe("true");
    });
  });

  describe("useAuth outside provider", () => {
    it("throws when used outside AuthProvider", () => {
      // Suppress console.error for this test
      const spy = vi.spyOn(console, "error").mockImplementation(() => {});

      function BadConsumer() {
        useAuth();
        return null;
      }

      expect(() => render(<BadConsumer />)).toThrow(
        "useAuth must be used within an AuthProvider"
      );

      spy.mockRestore();
    });
  });
});
