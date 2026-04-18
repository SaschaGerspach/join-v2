import { test, expect } from '@playwright/test';
import { createBoard, deleteBoard, createColumn } from './api';

let boardId: number;
let todoColumnId: number;
let doneColumnId: number;

test.beforeEach(async () => {
  const board = await createBoard(`Tasks ${Date.now()}`);
  boardId = board.id;
  todoColumnId = (await createColumn(boardId, 'To Do')).id;
  doneColumnId = (await createColumn(boardId, 'Done')).id;
});

test.afterEach(async () => {
  if (boardId) await deleteBoard(boardId);
});

test('create a task in a column', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  const todoCol = page.locator('.kanban-column', { hasText: 'To Do' });

  await todoCol.getByRole('button', { name: '+ Add Task' }).click();
  await page.locator('input.field-input[placeholder="Task title"]').fill('My first task');
  await page.getByRole('button', { name: 'Create Task' }).click();

  await expect(todoCol.locator('.task-card', { hasText: 'My first task' })).toBeVisible();
});

test('drag task from one column to another', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  const todoCol = page.locator('.kanban-column', { hasText: 'To Do' });
  const doneCol = page.locator('.kanban-column', { hasText: 'Done' });

  await todoCol.getByRole('button', { name: '+ Add Task' }).click();
  await page.locator('input.field-input[placeholder="Task title"]').fill('Drag me');
  await page.getByRole('button', { name: 'Create Task' }).click();

  const card = todoCol.locator('.task-card', { hasText: 'Drag me' });
  await expect(card).toBeVisible();

  const target = doneCol.locator('.task-list');
  await card.dragTo(target);

  await expect(doneCol.locator('.task-card', { hasText: 'Drag me' })).toBeVisible();
  await expect(todoCol.locator('.task-card', { hasText: 'Drag me' })).toHaveCount(0);
});

test('bulk-select and bulk-delete tasks', async ({ page }) => {
  await page.goto(`/boards/${boardId}`);
  const todoCol = page.locator('.kanban-column', { hasText: 'To Do' });

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
