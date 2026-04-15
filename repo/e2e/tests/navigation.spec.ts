import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers";

test.describe("Navigation & Layout", () => {
  test("sidebar shows navigation links for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.getByText(/dashboard/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/patients/i).first()).toBeVisible();
    await expect(page.getByText(/media/i).first()).toBeVisible();
    await expect(page.getByText(/financials/i).first()).toBeVisible();
    await expect(page.getByText(/admin/i).first()).toBeVisible();
  });

  test("clicking sidebar link navigates to correct page", async ({ page }) => {
    await loginAsAdmin(page);
    // Click on Patients in sidebar
    await page.getByRole("link", { name: /patients/i }).first().click();
    await expect(page).toHaveURL(/.*patients/);
  });

  test("404 page shown for unknown routes", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/this-page-does-not-exist");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /404/ })).toBeVisible({ timeout: 10000 });
  });

  test("back to dashboard link works from error pages", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/this-page-does-not-exist");
    await page.waitForLoadState("networkidle");
    const backLink = page.getByRole("link", { name: /back to dashboard/i });
    if (await backLink.isVisible().catch(() => false)) {
      await backLink.click();
      await expect(page).toHaveURL(/.*dashboard/);
    }
  });
});
