import { describe, it, expect, vi } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { ErrorBoundary } from "../ErrorBoundary";

function ThrowError(): JSX.Element {
  throw new Error("test error");
}

describe("ErrorBoundary", () => {
  // Suppress console.error for expected errors in tests
  const originalError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalError;
  });

  it("renders children when no error occurs", () => {
    renderWithProviders(
      <ErrorBoundary>
        <div>Child Content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText("Child Content")).toBeInTheDocument();
  });

  it("renders fallback UI when a child throws an error", () => {
    renderWithProviders(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("test error")).toBeInTheDocument();
  });

  it("resets error state when the Try Again button is clicked", async () => {
    let shouldThrow = true;

    function MaybeThrow() {
      if (shouldThrow) {
        throw new Error("test error");
      }
      return <div>Recovered Content</div>;
    }

    renderWithProviders(
      <ErrorBoundary>
        <MaybeThrow />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    shouldThrow = false;
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(screen.getByText("Recovered Content")).toBeInTheDocument();
  });
});
