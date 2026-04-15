import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers";

test.describe("Admin - Policies", () => {
  test("policies page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/policies");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /polic/i })).toBeVisible({ timeout: 15000 });
  });

  test("admin nav shows all sections", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/users");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/users/i).first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/throttling/i)).toBeVisible();
    await expect(page.getByText(/bulk export/i)).toBeVisible();
    await expect(page.getByText(/audit log/i)).toBeVisible();
    await expect(page.getByText(/policies/i)).toBeVisible();
  });

  test("export page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/export");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /patient records/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole("heading", { name: /media assets/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /financial records/i })).toBeVisible();
  });

  test("export requires sudo authentication", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/export");
    await page.waitForLoadState("networkidle");
    const exportBtn = page.getByRole("button", { name: /export csv/i }).first();
    await expect(exportBtn).toBeVisible({ timeout: 15000 });
    await exportBtn.click();
    await expect(
      page.getByRole("heading", { name: /confirm/i }).or(page.getByLabel(/password/i))
    ).toBeVisible({ timeout: 10000 });
  });
});
