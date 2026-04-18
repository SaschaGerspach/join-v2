import { test, expect } from '@playwright/test';
import { login } from './helpers';

test('create, open and delete a board via UI', async ({ page }) => {
  const title = `Board ${Date.now()}`;

  await login(page);
  await page.goto('/boards');
  await page.getByRole('button', { name: '+ New Board' }).click();
  await page.locator('.board-form input.form-input').fill(title);
  await page.getByRole('button', { name: 'Create', exact: true }).click();

  const card = page.locator('.board-card', { hasText: title });
  await expect(card).toBeVisible();

  await card.click();
  await expect(page).toHaveURL(/\/boards\/\d+$/);
  await expect(page.getByRole('heading', { name: title })).toBeVisible();

  await page.goto('/boards');
  await page.locator('.board-card', { hasText: title }).locator('.btn-delete').click();
  await page.locator('.dialog .btn-delete').click();
  await expect(page.locator('.board-card', { hasText: title })).toHaveCount(0);
});
