import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAs } from "./helpers";

test.describe("Media Workflow", () => {
  test("media upload page has watermark controls with correct defaults", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/media/upload");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/drag and drop|browse/i)).toBeVisible({ timeout: 10000 });
    // Watermark controls
    await expect(page.getByText(/clinic name/i)).toBeVisible();
    await expect(page.getByText(/date stamp/i)).toBeVisible();
    // Opacity default should be 35
    const opacityInput = page.locator('input[type="range"]').first();
    if (await opacityInput.isVisible().catch(() => false)) {
      const val = await opacityInput.inputValue();
      expect(val).toBe("35");
    }
  });

  test("media upload accepts only JPEG and PNG", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/media/upload");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/JPEG, PNG/)).toBeVisible({ timeout: 10000 });
    // Should NOT mention GIF or WebP
    await expect(page.getByText(/GIF/)).not.toBeVisible();
    await expect(page.getByText(/WebP/)).not.toBeVisible();
  });

  test("media library has upload link", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/media");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("link", { name: /upload/i })).toBeVisible({ timeout: 10000 });
  });

  test("compliance user cannot upload media", async ({ page }) => {
    await loginAs(page, "compliance");
    await page.goto("/media");
    await page.waitForLoadState("networkidle");
    // Compliance is not in the allowed roles for media
    await expect(page.getByRole("heading", { name: /403/i })).toBeVisible({
      timeout: 10000,
    });
  });

  test("clinician can access media library", async ({ page }) => {
    await loginAs(page, "clinician");
    await page.goto("/media");
    await page.waitForLoadState("networkidle");
    // Clinician should be able to view media
    await expect(page.locator("body")).not.toContainText(/403|forbidden/i);
  });
});
