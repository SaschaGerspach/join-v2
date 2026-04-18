import { test, expect } from '@playwright/test';
import { createBoard, deleteBoard } from './api';
import { login } from './helpers';

let boardId: number;

test.beforeEach(async ({ page }) => {
  const board = await createBoard(`Columns ${Date.now()}`);
  boardId = board.id;
  await login(page);
});

test.afterEach(async () => {
  if (boardId) await deleteBoard(boardId);
});

test('add a new column to a board', async ({ page }) => {
  const columnTitle = `Col ${Date.now()}`;
  await page.goto(`/boards/${boardId}`);

  await page.getByRole('button', { name: '+ Add Column' }).click();
  await page.locator('.column-form input.form-input').fill(columnTitle);
  await page.getByRole('button', { name: 'Add', exact: true }).click();

  await expect(page.locator('.column-title', { hasText: columnTitle })).toBeVisible();
});

test('rename column via double-click', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  await page.getByRole('button', { name: '+ Add Column' }).click();
  await page.locator('.column-form input.form-input').fill('Original');
  await page.getByRole('button', { name: 'Add', exact: true }).click();

  const title = page.locator('.column-title', { hasText: 'Original' });
  await expect(title).toBeVisible();
  await title.dblclick();
  await page.locator('.column-title-input').fill('Renamed');
  await page.locator('.column-title-input').press('Enter');

  await expect(page.locator('.column-title', { hasText: 'Renamed' })).toBeVisible();
});
