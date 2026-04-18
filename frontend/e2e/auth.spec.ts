import { test, expect } from '@playwright/test';

test.describe('auth (logged in via storageState)', () => {
  test('lands on summary when authenticated', async ({ page }) => {
    await page.goto('/summary');
    await expect(page).toHaveURL(/\/summary$/);
  });

  test('logout redirects to login', async ({ page }) => {
    await page.goto('/summary');
    await page.locator('.user-badge').click();
    await page.getByRole('button', { name: 'Log out' }).click();
    await expect(page).toHaveURL(/\/login$/);
  });
});

test.describe('auth (logged out)', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/summary');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('invalid credentials show error message', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.getByRole('button', { name: /log\s*in/i }).click();
    await expect(page.locator('.error-message').first()).toBeVisible();
  });
});
