import { describe, it, expect } from "vitest";
import { cn } from "../utils";

describe("cn()", () => {
  it("merges multiple class strings correctly", () => {
    const result = cn("px-4 py-2", "bg-primary text-white");
    expect(result).toBe("px-4 py-2 bg-primary text-white");
  });

  it("handles conditional classes via clsx syntax", () => {
    const isActive = true;
    const isDisabled = false;
    const result = cn("base", isActive && "active", isDisabled && "disabled");
    expect(result).toContain("base");
    expect(result).toContain("active");
    expect(result).not.toContain("disabled");
  });

  it("handles undefined and null gracefully", () => {
    const result = cn("base", undefined, null, false, "extra");
    expect(result).toBe("base extra");
  });
});
