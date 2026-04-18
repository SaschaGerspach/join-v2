import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { TEST_USER } from './global-setup';

test('login lands on summary', async ({ page }) => {
  await login(page);
  await page.goto('/summary');
  await expect(page).toHaveURL(/\/summary$/);
});

test('logout redirects to login', async ({ page }) => {
  await login(page);
  await page.goto('/summary');
  await page.locator('.user-badge').click();
  await page.getByRole('button', { name: 'Log out' }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test('unauthenticated user is redirected to login', async ({ page }) => {
  await page.goto('/summary');
  await expect(page).toHaveURL(/\/login$/);
});

test('invalid credentials show error message', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name="email"]', TEST_USER.email);
  await page.fill('input[name="password"]', 'wrongpassword');
  await page.getByRole('button', { name: /log\s*in/i }).click();
  await expect(page.locator('.error-message').first()).toBeVisible();
});
