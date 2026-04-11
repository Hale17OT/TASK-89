/** Idle warning shows after 13 minutes of inactivity */
export const IDLE_WARNING_MS = 13 * 60 * 1000;

/** Session expires after 15 minutes of inactivity */
export const IDLE_TIMEOUT_MS = 15 * 60 * 1000;

/** How often to check for idle state (every 30 seconds) */
export const IDLE_CHECK_INTERVAL_MS = 30 * 1000;

/** Session refresh interval (every 4 minutes) */
export const SESSION_REFRESH_INTERVAL_MS = 4 * 60 * 1000;

/** Local storage keys */
export const LS_KEYS = {
  THEME: "medrights-theme",
  REMEMBERED_USERNAME: "medrights-remembered-username",
  WORKSTATION_ID: "medrights-workstation-id",
} as const;

/** Application roles */
export const ROLES = {
  ADMIN: "admin",
  CLINICIAN: "clinician",
  FRONT_DESK: "front_desk",
  COMPLIANCE: "compliance",
} as const;

/** Role display labels */
export const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  clinician: "Clinician",
  front_desk: "Front Desk",
  compliance: "Compliance Officer",
} as const;

/** All available roles as an array */
export const ALL_ROLES = Object.values(ROLES);
