import { test, expect } from "@playwright/test";
import { loginAs, loginAsAdmin } from "./helpers";

test.describe("Dashboard", () => {
  test("admin dashboard shows all stat cards", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.getByText(/welcome back/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/patients/i).first()).toBeVisible();
    await expect(page.getByText(/media/i).first()).toBeVisible();
    await expect(page.getByText(/reports/i).first()).toBeVisible();
  });

  test("admin dashboard shows quick action links", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.getByText(/quick actions/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/register patient/i)).toBeVisible();
    await expect(page.getByText(/upload media/i)).toBeVisible();
  });

  test("front desk dashboard shows patient and order cards", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await expect(page.getByText(/welcome back/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/patients/i).first()).toBeVisible();
    await expect(page.getByText(/open orders/i)).toBeVisible();
  });

  test("dashboard displays user role", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.getByText(/logged in as/i)).toBeVisible({ timeout: 10000 });
  });
});
