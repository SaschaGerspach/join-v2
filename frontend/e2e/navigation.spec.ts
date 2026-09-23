import { test, expect } from '@playwright/test';

test.describe('Navigation (unauthenticated)', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('should redirect /boards to /login', async ({ page }) => {
    await page.goto('/boards');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /contacts to /login', async ({ page }) => {
    await page.goto('/contacts');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect /calendar to /login', async ({ page }) => {
    await page.goto('/calendar');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show not-found page for invalid routes', async ({ page }) => {
    await page.goto('/this-does-not-exist');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/this-does-not-exist$/);
    await expect(page.locator('body')).toContainText(/not found|404/i);
  });

  for (const path of ['/register', '/privacy', '/reset-password/uid/token', '/verify-email/uid/token']) {
    test(`should keep logged-out visitors on public page ${path}`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(new RegExp(`${path}$`));
    });
  }
});
