import { test, expect } from '@playwright/test';

test.describe('Navigation (unauthenticated)', () => {
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
    await expect(page.locator('body')).toContainText(/not found|404/i);
  });
});
