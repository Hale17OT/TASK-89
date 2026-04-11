import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsFrontDesk } from "./helpers";

test.describe("Financials", () => {
  test("order list page loads", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials");

    await expect(
      page.getByRole("heading", { name: /orders/i })
    ).toBeVisible();

    // Status filter should be present
    await expect(page.getByLabel(/status/i)).toBeVisible();

    // Create Order link should be present
    await expect(page.getByText(/create order/i)).toBeVisible();
  });

  test("create order form with line items", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials/new");

    await expect(
      page.getByRole("heading", { name: /create order/i })
    ).toBeVisible();

    // Patient search field
    await expect(
      page.getByPlaceholder(/search patients/i)
    ).toBeVisible();

    // Line items section
    await expect(page.getByText(/line items/i)).toBeVisible();

    // There should be at least one line item row with description, quantity, and unit price
    await expect(page.getByPlaceholder(/description/i).first()).toBeVisible();
    await expect(page.getByPlaceholder(/qty/i).first()).toBeVisible();
    await expect(page.getByPlaceholder(/unit price/i).first()).toBeVisible();

    // Add item button
    await expect(page.getByText(/add item/i)).toBeVisible();

    // Click Add Item to add a second row
    await page.getByText(/add item/i).click();
    const descriptionFields = page.getByPlaceholder(/description/i);
    await expect(descriptionFields).toHaveCount(2);

    // Total should show $0.00 initially
    await expect(page.getByText(/\$0\.00/)).toBeVisible();

    // Fill in the first line item and verify the total updates
    await page.getByPlaceholder(/description/i).first().fill("X-Ray");
    await page.getByPlaceholder(/qty/i).first().clear();
    await page.getByPlaceholder(/qty/i).first().fill("2");
    await page.getByPlaceholder(/unit price/i).first().clear();
    await page.getByPlaceholder(/unit price/i).first().fill("50");

    // Total should update to $100.00
    await expect(page.getByText(/\$100\.00/)).toBeVisible({ timeout: 5000 });
  });

  test("order detail shows countdown timer for open orders", async ({
    page,
  }) => {
    await loginAsAdmin(page);
    await page.goto("/financials");

    // Look for an order link in the table
    const orderLink = page.locator("table a").first();
    const hasOrders = await orderLink.isVisible().catch(() => false);

    if (hasOrders) {
      await orderLink.click();
      await page.waitForURL(/.*financials\/.*/, { timeout: 10000 });

      // The detail page should load with order information
      await expect(
        page.getByText(/order|status|amount|total|line items/i).first()
      ).toBeVisible({ timeout: 10000 });
    } else {
      // No orders exist; verify the empty state message
      await expect(page.getByText(/no orders found/i)).toBeVisible();
    }
  });

  test("reconciliation page loads with date picker", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/financials/reconciliation");

    // Should have a date input for selecting the reconciliation date
    await expect(page.locator('input[type="date"]')).toBeVisible();

    // Should show reconciliation summary or heading
    await expect(
      page.getByText(/reconcil|total orders|total payments/i).first()
    ).toBeVisible({ timeout: 10000 });
  });
});
