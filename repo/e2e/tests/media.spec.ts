import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers";

test.describe("Media", () => {
  test("media library page loads", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/media");

    await expect(
      page.getByRole("heading", { name: /media library/i })
    ).toBeVisible();

    // Search and filter controls should be present
    await expect(
      page.getByPlaceholder(/search/i).or(page.locator('input[type="text"]').first())
    ).toBeVisible();
  });

  test("media upload page has file dropzone and watermark controls", async ({
    page,
  }) => {
    await loginAsAdmin(page);
    await page.goto("/media/upload");

    await expect(
      page.getByRole("heading", { name: /upload media/i })
    ).toBeVisible();

    // Dropzone area should be visible
    await expect(
      page.getByText(/drag and drop|click to browse/i)
    ).toBeVisible();

    // Watermark settings section
    await expect(page.getByText(/watermark settings/i)).toBeVisible();

    // Clinic name input
    await expect(
      page.getByPlaceholder(/clinic name/i)
    ).toBeVisible();

    // Date stamp checkbox
    await expect(page.getByText(/include date stamp/i)).toBeVisible();

    // Opacity slider
    await expect(page.getByText(/opacity/i)).toBeVisible();
    await expect(page.locator('input[type="range"]')).toBeVisible();

    // Upload button should be present but disabled (no file selected)
    const uploadButton = page.getByRole("button", { name: /upload media/i });
    await expect(uploadButton).toBeVisible();
    await expect(uploadButton).toBeDisabled();
  });

  test("watermark opacity slider defaults to 35%", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/media/upload");

    // The opacity label should show 35%
    await expect(page.getByText(/opacity:\s*35%/i)).toBeVisible();

    // The range input should have value 35
    const slider = page.locator('input[type="range"]');
    await expect(slider).toHaveValue("35");
  });
});
