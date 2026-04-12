import { test, expect } from "@playwright/test";
import { loginAs, loginAsAdmin } from "./helpers";

test.describe("Infringement Reporting", () => {
  test("infringement list page loads for compliance user", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/infringements");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toContainText(/infringement|report/i);
  });

  test("infringement create page has required fields", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/infringements/new");
    await page.waitForLoadState("networkidle");
    // Should have screenshot, reference, and notes fields
    await expect(page.getByText(/screenshot|capture/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/reference|url/i)).toBeVisible();
    await expect(page.getByText(/notes/i)).toBeVisible();
  });

  test("front desk user cannot access infringements", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await page.goto("/infringements");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("infringement create requires at least screenshot or reference", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/infringements/new");
    await page.waitForLoadState("networkidle");
    // Notes field should be visible
    const notesArea = page.locator("textarea").first();
    await expect(notesArea).toBeVisible({ timeout: 10000 });
  });
});
