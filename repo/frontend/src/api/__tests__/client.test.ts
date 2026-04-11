import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock localStorage before importing the module
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] ?? null),
  };
})();

Object.defineProperty(globalThis, "localStorage", { value: localStorageMock });

// Provide crypto.randomUUID for jsdom
if (!globalThis.crypto?.randomUUID) {
  Object.defineProperty(globalThis, "crypto", {
    value: {
      ...globalThis.crypto,
      randomUUID: () => "00000000-1111-4222-8333-444444444444",
    },
  });
}

describe("apiClient", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.resetModules();
  });

  it("has the correct baseURL", async () => {
    const { default: apiClient } = await import("../client");
    expect(apiClient.defaults.baseURL).toBe("/api/v1/");
  });

  it("has CSRF cookie name configured for withCredentials", async () => {
    const { default: apiClient } = await import("../client");
    expect(apiClient.defaults.withCredentials).toBe(true);
    expect(apiClient.defaults.xsrfCookieName).toBe("medrights_csrf");
    expect(apiClient.defaults.xsrfHeaderName).toBe("X-CSRFToken");
  });

  it("generates a UUID workstation ID and persists it to localStorage", async () => {
    // Import the module fresh so it runs getWorkstationId on first interceptor call
    const { default: apiClient } = await import("../client");

    // The workstation ID is set lazily via the request interceptor.
    // Simulate a request interceptor run by manually invoking it.
    const interceptor = (apiClient.interceptors.request as any).handlers[0];
    const config = { headers: {} as Record<string, string> };
    const result = interceptor.fulfilled(config);

    expect(result.headers["X-Workstation-ID"]).toBeTruthy();
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "medrights-workstation-id",
      expect.any(String)
    );

    // Subsequent calls should reuse the same ID
    const config2 = { headers: {} as Record<string, string> };
    const result2 = interceptor.fulfilled(config2);
    expect(result2.headers["X-Workstation-ID"]).toBe(
      result.headers["X-Workstation-ID"]
    );
  });
});
