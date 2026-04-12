import { type Page, expect } from "@playwright/test";

/**
 * Log in as a specific user via the login page.
 * Waits for navigation to /dashboard before returning.
 */
export async function loginAs(
  page: Page,
  username: string,
  password = "MedRights2026!"
) {
  await page.goto("/login");
  const usernameField = page.getByRole("textbox", { name: /username/i });
  await expect(usernameField).toBeVisible({ timeout: 30000 });
  await usernameField.fill(username);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  // Wait for redirect away from /login (may go to / then /dashboard)
  await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 45000 });
  // Wait for the target page to finish loading its data
  await page.waitForLoadState("networkidle");
}

/**
 * Log in as the admin user (convenience wrapper).
 */
export async function loginAsAdmin(page: Page) {
  return loginAs(page, "admin");
}

/**
 * Log in as the front desk user.
 */
export async function loginAsFrontDesk(page: Page) {
  return loginAs(page, "frontdesk");
}

/**
 * Get the API base URL from the environment or fall back to the default.
 */
export function getApiUrl(): string {
  return process.env.API_URL || "http://localhost:8000";
}
