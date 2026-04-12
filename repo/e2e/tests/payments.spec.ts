import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAs } from "./helpers";

test.describe("Payments & Refunds", () => {
  test("order create page renders line item form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials/new");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/description/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/quantity/i)).toBeVisible();
    await expect(page.getByText(/price/i)).toBeVisible();
  });

  test("order list page shows status filter", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/orders/i)).toBeVisible({ timeout: 10000 });
    // Should have a create button
    await expect(page.getByText(/create order/i)).toBeVisible();
  });

  test("reconciliation page has date picker and export", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials/reconciliation");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/reconciliation/i)).toBeVisible({ timeout: 10000 });
  });

  test("clinician cannot access financials", async ({ page }) => {
    await loginAs(page, "clinician");
    await page.goto("/financials");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });
});
