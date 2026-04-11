import React from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { AuthContext } from "@/contexts/AuthContext";
import type { User } from "@/api/types/auth.types";

interface WrapperOptions {
  route?: string;
  user?: User | null;
}

/**
 * Render a component wrapped with all the providers needed by the app:
 * QueryClientProvider, MemoryRouter, and AuthContext.
 */
export function renderWithProviders(
  ui: React.ReactElement,
  options?: WrapperOptions & Omit<RenderOptions, "wrapper">
) {
  const { route = "/", user = null, ...renderOptions } = options ?? {};

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const authValue = {
    user,
    isLoading: false,
    idleWarningVisible: false,
    reauthRequired: false,
    login: async () => {},
    logout: async () => {},
    dispatch: () => {},
  };

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={authValue as any}>
          <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
        </AuthContext.Provider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

export { default as userEvent } from "@testing-library/user-event";
export { screen, waitFor } from "@testing-library/react";
