import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useIdleTimer } from "../useIdleTimer";

vi.mock("@/api/endpoints/auth", () => ({
  refreshSession: vi.fn().mockResolvedValue({}),
}));

describe("useIdleTimer", () => {
  it("can be instantiated without error when enabled", () => {
    const onWarning = vi.fn();
    const onExpire = vi.fn();

    const { result } = renderHook(() =>
      useIdleTimer({ onWarning, onExpire, enabled: true })
    );

    expect(result.current.resetActivity).toBeDefined();
    expect(typeof result.current.resetActivity).toBe("function");
  });

  it("can be instantiated without error when disabled", () => {
    const onWarning = vi.fn();
    const onExpire = vi.fn();

    const { result } = renderHook(() =>
      useIdleTimer({ onWarning, onExpire, enabled: false })
    );

    expect(result.current.resetActivity).toBeDefined();
    expect(typeof result.current.resetActivity).toBe("function");
  });
});
