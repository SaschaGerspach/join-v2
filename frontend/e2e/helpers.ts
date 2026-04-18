import { Page, expect } from '@playwright/test';
import { TEST_USER } from './global-setup';

export async function login(page: Page): Promise<void> {
  await page.goto('/login');
  await page.fill('input[name="email"]', TEST_USER.email);
  await page.fill('input[name="password"]', TEST_USER.password);
  await page.getByRole('button', { name: /log\s*in/i }).click();
  await expect(page).toHaveURL(/\/(summary|boards)/);
}
