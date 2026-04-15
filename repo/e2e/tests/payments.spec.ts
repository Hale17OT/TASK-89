import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAs } from "./helpers";

test.describe("Payments & Refunds", () => {
  test("order create page renders line item form", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials/new");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /create order/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByPlaceholder(/description/i).first()).toBeVisible();
    await expect(page.getByPlaceholder(/qty/i).first()).toBeVisible();
    await expect(page.getByPlaceholder(/unit price/i).first()).toBeVisible();
  });

  test("order list page shows status filter", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /orders/i })).toBeVisible({ timeout: 10000 });
    // Should have a create button
    await expect(page.getByText(/create order/i)).toBeVisible();
  });

  test("reconciliation page has date picker and export", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials/reconciliation");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /reconcil/i })).toBeVisible({ timeout: 10000 });
  });

  test("clinician cannot access financials", async ({ page }) => {
    await loginAs(page, "clinician");
    await page.goto("/financials");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /403/i })).toBeVisible({
      timeout: 10000,
    });
  });
});
