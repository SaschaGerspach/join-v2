import { test, expect } from '@playwright/test';
import { createBoard, deleteBoard, createColumn } from './api';
import { login } from './helpers';

let boardId: number;

test.beforeEach(async ({ page }) => {
  const board = await createBoard(`Detail ${Date.now()}`);
  boardId = board.id;
  await createColumn(boardId, 'To Do');
  await login(page);
  await page.goto(`/boards/${boardId}`);

  const col = page.locator('.kanban-column').filter({ has: page.locator('.column-title', { hasText: /^To Do$/ }) });
  await col.getByRole('button', { name: '+ Add Task' }).click();
  await page.locator('input.field-input[placeholder="Task title"]').fill('Detail Task');
  await page.getByRole('button', { name: 'Create Task' }).click();
  await expect(col.locator('.task-card', { hasText: 'Detail Task' })).toBeVisible();
});

test.afterEach(async () => {
  if (boardId) await deleteBoard(boardId);
});

test('open task detail modal by clicking task card', async ({ page }) => {
  await page.locator('.task-card', { hasText: 'Detail Task' }).click();
  await expect(page.locator('.modal-card')).toBeVisible();
  await expect(page.locator('.modal-title-input')).toHaveValue('Detail Task');
});

test('edit task title in detail modal', async ({ page }) => {
  await page.locator('.task-card', { hasText: 'Detail Task' }).click();
  await page.locator('.modal-title-input').fill('Updated Title');
  await page.getByRole('button', { name: /save/i }).click();
  await expect(page.locator('.task-card', { hasText: 'Updated Title' })).toBeVisible();
});

test('delete task from detail modal', async ({ page }) => {
  await page.locator('.task-card', { hasText: 'Detail Task' }).click();
  await page.getByRole('button', { name: /delete/i }).click();
  await expect(page.locator('.task-card', { hasText: 'Detail Task' })).toHaveCount(0);
});
