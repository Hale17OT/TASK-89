import { describe, it, expect } from "vitest";
import { IDLE_WARNING_MS, IDLE_TIMEOUT_MS, ROLES } from "../constants";

describe("constants", () => {
  it("IDLE_WARNING_MS is 13 minutes (780000ms)", () => {
    expect(IDLE_WARNING_MS).toBe(13 * 60 * 1000);
    expect(IDLE_WARNING_MS).toBe(780000);
  });

  it("IDLE_TIMEOUT_MS is 15 minutes (900000ms)", () => {
    expect(IDLE_TIMEOUT_MS).toBe(15 * 60 * 1000);
    expect(IDLE_TIMEOUT_MS).toBe(900000);
  });

  it("ROLES contains exactly admin, clinician, front_desk, compliance", () => {
    expect(ROLES).toEqual({
      ADMIN: "admin",
      CLINICIAN: "clinician",
      FRONT_DESK: "front_desk",
      COMPLIANCE: "compliance",
    });

    const values = Object.values(ROLES);
    expect(values).toHaveLength(4);
    expect(values).toContain("admin");
    expect(values).toContain("clinician");
    expect(values).toContain("front_desk");
    expect(values).toContain("compliance");
  });
});
