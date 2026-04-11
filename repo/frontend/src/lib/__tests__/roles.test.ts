import { describe, it, expect } from "vitest";
import { hasRole, getRoleLabel, ROLES } from "../roles";

describe("hasRole()", () => {
  it("returns true when the user role matches an allowed role", () => {
    expect(hasRole("admin", ["admin", "clinician"])).toBe(true);
    expect(hasRole("clinician", ["admin", "clinician"])).toBe(true);
  });

  it("returns false when the user role does not match any allowed role", () => {
    expect(hasRole("viewer", ["admin", "clinician"])).toBe(false);
    expect(hasRole("front_desk", ["admin"])).toBe(false);
  });

  it('returns true for any valid role when allowedRoles is "all"', () => {
    expect(hasRole("admin", "all")).toBe(true);
    expect(hasRole("clinician", "all")).toBe(true);
    expect(hasRole("front_desk", "all")).toBe(true);
    expect(hasRole("compliance", "all")).toBe(true);
  });

  it("returns false for undefined or null user role", () => {
    expect(hasRole(undefined, ["admin"])).toBe(false);
    expect(hasRole(null, ["admin"])).toBe(false);
    expect(hasRole(undefined, "all")).toBe(false);
  });
});

describe("getRoleLabel()", () => {
  it("returns the correct display label for each role", () => {
    expect(getRoleLabel("admin")).toBe("Administrator");
    expect(getRoleLabel("clinician")).toBe("Clinician");
    expect(getRoleLabel("front_desk")).toBe("Front Desk");
    expect(getRoleLabel("compliance")).toBe("Compliance Officer");
  });

  it("returns the raw role string when no label is defined", () => {
    expect(getRoleLabel("unknown_role")).toBe("unknown_role");
  });
});
