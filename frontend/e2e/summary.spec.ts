import { test, expect } from '@playwright/test';
import { login } from './helpers';

test('summary page shows greeting and stats', async ({ page }) => {
  await login(page);
  await page.goto('/summary');

  await expect(page.locator('.greeting')).toBeVisible();
  await expect(page.locator('.stat-card', { hasText: 'Boards' })).toBeVisible();
  await expect(page.locator('.stat-card', { hasText: 'Tasks in total' })).toBeVisible();
});

test('clicking boards stat navigates to boards page', async ({ page }) => {
  await login(page);
  await page.goto('/summary');

  await page.locator('.stat-card', { hasText: 'Boards' }).click();
  await expect(page).toHaveURL(/\/boards$/);
});
