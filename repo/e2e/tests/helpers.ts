import { type Page, expect } from "@playwright/test";

/**
 * Attempt to fill and submit the login form.
 * Returns true if the page navigated away from /login, false otherwise.
 */
async function attemptLogin(
  page: Page,
  username: string,
  password: string,
  timeout: number
): Promise<boolean> {
  const usernameField = page.getByRole("textbox", { name: /username/i });
  await expect(usernameField).toBeVisible({ timeout: 10000 });
  await usernameField.clear();
  await usernameField.fill(username);
  await page.getByLabel(/password/i).fill(password);

  const submitBtn = page.getByRole("button", { name: /sign in/i });
  await expect(submitBtn).toBeEnabled({ timeout: 5000 });
  await submitBtn.click();

  try {
    await page.waitForURL((url) => !url.pathname.includes("/login"), {
      timeout,
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Log in as a specific user via the login page.
 * Waits for navigation to /dashboard before returning.
 * Retries once if the first attempt fails (handles transient backend slowness).
 */
export async function loginAs(
  page: Page,
  username: string,
  password = "MedRights2026!"
) {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // First attempt with a shorter timeout
  let success = await attemptLogin(page, username, password, 15000);

  if (!success) {
    // Backend may have been briefly overloaded - reload and retry
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    success = await attemptLogin(page, username, password, 20000);
    if (!success) {
      throw new Error(`Login as '${username}' failed after retry`);
    }
  }

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
