import { ROLES, ROLE_LABELS, ALL_ROLES } from "./constants";

export type Role = (typeof ROLES)[keyof typeof ROLES];

/**
 * Check if a user role is included in the list of allowed roles.
 * Pass "all" to allow any role.
 */
export function hasRole(
  userRole: string | undefined | null,
  allowedRoles: Role[] | "all"
): boolean {
  if (!userRole) return false;
  if (allowedRoles === "all") return ALL_ROLES.includes(userRole as Role);
  return allowedRoles.includes(userRole as Role);
}

/**
 * Get the display label for a role.
 */
export function getRoleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

export { ROLES, ROLE_LABELS, ALL_ROLES };
