import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers";

test.describe("Role Boundary Enforcement (E2E)", () => {
  test("clinician cannot access admin pages", async ({ page }) => {
    await loginAs(page, "clinician");
    await page.goto("/admin/users");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("clinician cannot access financials", async ({ page }) => {
    await loginAs(page, "clinician");
    await page.goto("/financials");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("clinician can access patients", async ({ page }) => {
    await loginAs(page, "clinician");
    await page.goto("/patients");
    await expect(page.locator("body")).not.toContainText(/403|forbidden/i);
  });

  test("compliance can access audit log", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/audit");
    await expect(page.getByText(/audit/i)).toBeVisible({ timeout: 10000 });
    await expect(page.locator("body")).not.toContainText(/403|forbidden/i);
  });

  test("compliance cannot access patients", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/patients");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("front desk can access patients", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await page.goto("/patients");
    await page.waitForLoadState("networkidle");
    // Wait for page content to render before checking
    await page.waitForTimeout(1000);
    await expect(page.locator("body")).not.toContainText(/403|forbidden/i);
  });

  test("front desk can access financials", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await page.goto("/financials");
    await expect(page.locator("body")).not.toContainText(/403|forbidden/i);
  });

  test("front desk cannot access audit log", async ({ page }) => {
    await loginAs(page, "frontdesk");
    await page.goto("/audit");
    await expect(page.getByText(/403|access denied|forbidden|permission/i)).toBeVisible({
      timeout: 10000,
    });
  });
});
