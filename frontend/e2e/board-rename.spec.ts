import { test, expect } from '@playwright/test';
import { createBoard, deleteBoard } from './api';
import { login } from './helpers';

let boardId: number;

test.beforeEach(async ({ page }) => {
  const board = await createBoard(`Rename ${Date.now()}`);
  boardId = board.id;
  await login(page);
  await page.goto(`/boards/${boardId}`);
});

test.afterEach(async () => {
  if (boardId) await deleteBoard(boardId);
});

test('rename board title via double-click', async ({ page }) => {
  const heading = page.locator('.board-detail-header h1');
  await expect(heading).toBeVisible();

  await heading.dblclick();
  const input = page.locator('input.board-title-input');
  await expect(input).toBeVisible();
  await input.fill('New Board Name');
  await input.press('Enter');

  await expect(page.locator('.board-detail-header h1')).toHaveText('New Board Name');
});
