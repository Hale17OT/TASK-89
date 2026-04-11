import { test, expect } from "@playwright/test";
import { loginAsAdmin } from "./helpers";

test.describe("Admin", () => {
  test("user management page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/users");

    // Should see a heading or content related to user management
    await expect(
      page.getByText(/user management|manage users|users/i).first()
    ).toBeVisible({ timeout: 10000 });

    // Should show a list of users or a create user option
    await expect(
      page.getByText(/create|add user|username|role/i).first()
    ).toBeVisible({ timeout: 10000 });
  });

  test("audit log page loads with filters", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/audit-log");

    await expect(
      page.getByRole("heading", { name: /audit log/i })
    ).toBeVisible();

    // Event type filter dropdown
    await expect(
      page.locator("select").first()
    ).toBeVisible();

    // Date range filters
    const dateInputs = page.locator('input[type="date"]');
    await expect(dateInputs.first()).toBeVisible();

    // Verify chain integrity button
    await expect(
      page.getByRole("button", { name: /verify chain/i })
    ).toBeVisible();
  });

  test("throttling page shows blacklist info", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin/throttling");

    await expect(
      page.getByRole("heading", { name: /throttling|blacklist/i })
    ).toBeVisible();

    // Should show throttle rules information
    await expect(
      page.getByText(/failed logins|lockout|blacklist/i).first()
    ).toBeVisible();

    // Should show either a list of blacklisted workstations or a "no blacklisted" message
    await expect(
      page.getByText(/no blacklisted|workstation|operating normally/i).first()
    ).toBeVisible({ timeout: 10000 });
  });
});
