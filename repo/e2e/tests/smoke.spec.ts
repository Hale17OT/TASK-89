import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers";

test.describe("Smoke Tests", () => {
  test("frontend loads login page", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /medrights/i })).toBeVisible();
  });

  test("health endpoint returns 200", async ({ request }) => {
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    const response = await request.get(`${apiUrl}/api/v1/health/`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("ok");
  });

  test("unauthenticated API returns 403", async ({ request }) => {
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    const response = await request.get(`${apiUrl}/api/v1/patients/`);
    expect(response.status()).toBe(403);
  });

  test("login with valid credentials redirects to dashboard", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page).toHaveURL(/dashboard/);
  });

  test("login with invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await page.getByRole("textbox", { name: /username/i }).fill("admin");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/invalid|error|unexpected/i).first()).toBeVisible({ timeout: 10000 });
  });
});
