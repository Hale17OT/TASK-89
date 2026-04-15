import { test, expect } from "@playwright/test";
import { loginAs, loginAsAdmin } from "./helpers";

test.describe("Reports & Outbox", () => {
  test("subscription list page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/subscription|report/i).first()).toBeVisible({ timeout: 10000 });
  });

  test("subscription list has New Subscription and View Outbox buttons", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/new subscription/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/view outbox/i)).toBeVisible();
  });

  test("subscription create form has required fields", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports/new");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/name/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByLabel(/report type/i)).toBeVisible();
    await expect(page.getByText(/schedule/i).first()).toBeVisible();
    await expect(page.getByText(/format/i).first()).toBeVisible();
  });

  test("outbox dashboard page loads", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports/outbox");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/outbox/i).first()).toBeVisible({ timeout: 10000 });
  });

  test("front desk user cannot access reports", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await page.goto("/reports");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /403/i })).toBeVisible({
      timeout: 10000,
    });
  });

  test("compliance user can access reports", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/reports");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/subscription|report/i).first()).toBeVisible({ timeout: 10000 });
  });
});
