import { test, expect } from '@playwright/test';
import { createBoard, deleteBoard, createColumn } from './api';
import { login } from './helpers';

let boardId: number;

test.beforeEach(async ({ page }) => {
  const board = await createBoard(`Tasks ${Date.now()}`);
  boardId = board.id;
  await createColumn(boardId, 'To Do');
  await createColumn(boardId, 'Done');
  await login(page);
});

test.afterEach(async () => {
  if (boardId) await deleteBoard(boardId);
});

test('create a task in a column', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  const todoCol = page.locator('.kanban-column').filter({ has: page.locator('.column-title', { hasText: /^To Do$/ }) });

  await todoCol.getByRole('button', { name: '+ Add Task' }).click();
  await page.locator('input.field-input[placeholder="Task title"]').fill('My first task');
  await page.getByRole('button', { name: 'Create Task' }).click();

  await expect(todoCol.locator('.task-card', { hasText: 'My first task' })).toBeVisible();
});

test('move task between columns via bulk-move', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  const todoCol = page.locator('.kanban-column').filter({ has: page.locator('.column-title', { hasText: /^To Do$/ }) });
  const doneCol = page.locator('.kanban-column').filter({ has: page.locator('.column-title', { hasText: /^Done$/ }) });

  await todoCol.getByRole('button', { name: '+ Add Task' }).click();
  await page.locator('input.field-input[placeholder="Task title"]').fill('Movable');
  await page.getByRole('button', { name: 'Create Task' }).click();
  await expect(todoCol.locator('.task-card', { hasText: 'Movable' })).toBeVisible();

  await todoCol.locator('.task-card', { hasText: 'Movable' }).locator('.task-select-checkbox').click();
  await page.locator('.bulk-toolbar select.filter-select').selectOption({ label: 'Done' });
  await page.locator('.bulk-toolbar .btn-bulk-move').click();

  await expect(doneCol.locator('.task-card', { hasText: 'Movable' })).toBeVisible();
  await expect(todoCol.locator('.task-card', { hasText: 'Movable' })).toHaveCount(0);
});

test('bulk-select and bulk-delete tasks', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  const todoCol = page.locator('.kanban-column').filter({ has: page.locator('.column-title', { hasText: /^To Do$/ }) });

  for (const title of ['Task A', 'Task B', 'Task C']) {
    await todoCol.getByRole('button', { name: '+ Add Task' }).click();
    await page.locator('input.field-input[placeholder="Task title"]').fill(title);
    await page.getByRole('button', { name: 'Create Task' }).click();
    await expect(todoCol.locator('.task-card', { hasText: title })).toBeVisible();
  }

  await todoCol.locator('.task-card', { hasText: 'Task A' }).locator('.task-select-checkbox').click();
  await todoCol.locator('.task-card', { hasText: 'Task B' }).locator('.task-select-checkbox').click();

  await expect(page.locator('.bulk-toolbar')).toContainText('2 selected');

  await page.locator('.bulk-toolbar .btn-bulk-delete').click();
  await page.locator('.dialog .btn-delete').click();

  await expect(todoCol.locator('.task-card', { hasText: 'Task A' })).toHaveCount(0);
  await expect(todoCol.locator('.task-card', { hasText: 'Task B' })).toHaveCount(0);
  await expect(todoCol.locator('.task-card', { hasText: 'Task C' })).toBeVisible();
});
