import { test, expect } from "@playwright/test";
import { loginAs, loginAsAdmin } from "./helpers";

test.describe("Reports & Outbox", () => {
  test("subscription list page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
    await expect(page.getByText(/subscription|report/i)).toBeVisible({ timeout: 10000 });
  });

  test("subscription list has New Subscription and View Outbox buttons", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports");
    await expect(page.getByText(/new subscription/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/view outbox/i)).toBeVisible();
  });

  test("subscription create form has required fields", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports/new");
    await expect(page.getByText(/name/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/report type/i)).toBeVisible();
    await expect(page.getByText(/schedule/i)).toBeVisible();
    await expect(page.getByText(/format/i)).toBeVisible();
  });

  test("outbox dashboard page loads", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/reports/outbox");
    await expect(page.getByText(/outbox|report/i)).toBeVisible({ timeout: 10000 });
  });

  test("front desk user cannot access reports", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await page.goto("/reports");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("compliance user can access reports", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/reports");
    await expect(page.getByText(/subscription|report/i)).toBeVisible({ timeout: 10000 });
  });
});
