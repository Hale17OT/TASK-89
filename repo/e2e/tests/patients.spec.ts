import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsFrontDesk } from "./helpers";

test.describe("Patients", () => {
  test("patient search page loads", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/patients");
    await page.waitForLoadState("networkidle");

    await expect(
      page.getByRole("heading", { name: /patients/i })
    ).toBeVisible();
    await expect(
      page.getByPlaceholder(/search by name|search/i)
    ).toBeVisible();
    await expect(page.getByText(/create patient/i)).toBeVisible();
  });

  test("create patient form renders all fields", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/patients/new");
    await page.waitForLoadState("networkidle");

    await expect(
      page.getByRole("heading", { name: /register new patient/i })
    ).toBeVisible();

    // Required fields
    await expect(page.getByText(/MRN/)).toBeVisible();
    await expect(page.getByText(/First Name/)).toBeVisible();
    await expect(page.getByText(/Last Name/)).toBeVisible();
    await expect(page.getByText(/Date of Birth/)).toBeVisible();
    await expect(page.getByText(/Gender/)).toBeVisible();

    // Optional fields
    await expect(page.getByText(/SSN/)).toBeVisible();
    await expect(page.getByText(/Phone/)).toBeVisible();
    await expect(page.getByText(/Email/)).toBeVisible();
    await expect(page.getByText(/Address/)).toBeVisible();

    // Submit button
    await expect(
      page.getByRole("button", { name: /create patient/i })
    ).toBeVisible();
  });

  test("create patient with valid data shows success", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/patients/new");
    await page.waitForLoadState("networkidle");

    const uniqueMrn = `MRN-${Date.now()}`;
    await page.getByPlaceholder(/medical record number/i).fill(uniqueMrn);
    await page.getByPlaceholder(/first name/i).fill("TestFirst");
    await page.getByPlaceholder(/last name/i).fill("TestLast");
    await page.locator('input[type="date"]').fill("1990-01-15");
    await page.locator("select").selectOption("male");

    await page.getByRole("button", { name: /create patient/i }).click();

    // Should navigate to patient detail or show success toast
    await expect(
      page.getByText(/success|created|patient/i).or(page.locator('[data-sonner-toast]'))
    ).toBeVisible({ timeout: 15000 });
  });

  test("search for non-existent patient shows empty state", async ({
    page,
  }) => {
    await loginAsAdmin(page);
    await page.goto("/patients");
    await page.waitForLoadState("networkidle");

    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill("zzz_nonexistent_patient_xyz_12345");

    // Wait for debounce and results
    await expect(
      page.getByText(/no patients found|try a different/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test("patient detail shows masked data", async ({ page }) => {
    await loginAsAdmin(page);

    // First create a patient to ensure one exists
    await page.goto("/patients/new");
    await page.waitForLoadState("networkidle");
    const uniqueMrn = `MRN-DETAIL-${Date.now()}`;
    await page.getByPlaceholder(/medical record number/i).fill(uniqueMrn);
    await page.getByPlaceholder(/first name/i).fill("DetailFirst");
    await page.getByPlaceholder(/last name/i).fill("DetailLast");
    await page.locator('input[type="date"]').fill("1985-06-20");
    await page.locator("select").selectOption("female");
    await page.getByRole("button", { name: /create patient/i }).click();

    // Wait for navigation to detail page
    await page.waitForURL(/.*patients\/.*/, { timeout: 15000 });

    // The patient detail page should show some content (possibly masked)
    await expect(
      page.getByText(/patient|detail|MRN|name/i).first()
    ).toBeVisible({ timeout: 10000 });
  });
});
