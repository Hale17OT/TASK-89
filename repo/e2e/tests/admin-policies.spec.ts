import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAs } from "./helpers";

test.describe("Admin - Policies", () => {
  test("policies page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/policies");
    await expect(page.getByText(/polic/i)).toBeVisible({ timeout: 10000 });
  });

  test("admin nav shows all sections", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/users");
    await expect(page.getByText(/users/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/throttling/i)).toBeVisible();
    await expect(page.getByText(/bulk export/i)).toBeVisible();
    await expect(page.getByText(/audit log/i)).toBeVisible();
    await expect(page.getByText(/policies/i)).toBeVisible();
  });

  test("export page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/export");
    await expect(page.getByText(/export/i).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/patient records/i)).toBeVisible();
    await expect(page.getByText(/media assets/i)).toBeVisible();
    await expect(page.getByText(/financial records/i)).toBeVisible();
  });

  test("export requires sudo authentication", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/export");
    // Click an export button
    const exportBtn = page.getByRole("button", { name: /export csv/i }).first();
    await expect(exportBtn).toBeVisible({ timeout: 10000 });
    await exportBtn.click();
    // Should show sudo/confirmation dialog
    await expect(page.getByText(/re-authenticat|password|confirm/i)).toBeVisible({
      timeout: 10000,
    });
  });
});
