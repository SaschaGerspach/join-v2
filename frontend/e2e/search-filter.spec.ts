import { test, expect } from '@playwright/test';
import { createBoard, deleteBoard, createColumn } from './api';
import { login } from './helpers';

let boardId: number;

test.beforeEach(async ({ page }) => {
  const board = await createBoard(`Filter ${Date.now()}`);
  boardId = board.id;
  await createColumn(boardId, 'To Do');
  await login(page);
  await page.goto(`/boards/${boardId}`);

  const col = page.locator('.kanban-column').filter({ has: page.locator('.column-title', { hasText: /^To Do$/ }) });
  for (const title of ['Alpha Task', 'Beta Task', 'Gamma Task']) {
    await col.getByRole('button', { name: '+ Add Task' }).click();
    await page.locator('input.field-input[placeholder="Task title"]').fill(title);
    await page.getByRole('button', { name: 'Create Task' }).click();
    await expect(col.locator('.task-card', { hasText: title })).toBeVisible();
  }
});

test.afterEach(async () => {
  if (boardId) await deleteBoard(boardId);
});

test('search filters tasks by title', async ({ page }) => {
  await page.locator('input.search-input').fill('Beta');
  await expect(page.locator('.task-card', { hasText: 'Beta Task' })).toBeVisible();
  await expect(page.locator('.task-card', { hasText: 'Alpha Task' })).toHaveCount(0);
  await expect(page.locator('.task-card', { hasText: 'Gamma Task' })).toHaveCount(0);
});

test('clearing search shows all tasks again', async ({ page }) => {
  await page.locator('input.search-input').fill('Beta');
  await expect(page.locator('.task-card')).toHaveCount(1);
  await page.locator('input.search-input').fill('');
  await expect(page.locator('.task-card')).toHaveCount(3);
});

test('search with no matches shows empty columns', async ({ page }) => {
  await page.locator('input.search-input').fill('NonexistentXYZ');
  await expect(page.locator('.task-card')).toHaveCount(0);
});
