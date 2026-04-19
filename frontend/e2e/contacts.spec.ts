import { test, expect } from '@playwright/test';
import { login } from './helpers';

test.beforeEach(async ({ page }) => {
  await login(page);
  await page.goto('/contacts');
});

test('create a new contact', async ({ page }) => {
  const name = `E2E-${Date.now()}`;
  await page.getByRole('button', { name: '+ New Contact' }).click();
  await page.locator('input.field-input[placeholder="First name"]').fill(name);
  await page.locator('input.field-input[placeholder="Last name"]').fill('Test');
  await page.locator('input.field-input[placeholder="Email address"]').fill(`${name}@test.com`);
  await page.getByRole('button', { name: 'Create' }).click();

  await expect(page.locator('.contact-list-name', { hasText: `${name} Test` })).toBeVisible();

  // cleanup
  await page.locator('.contact-list-item', { hasText: `${name} Test` }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.locator('.dialog .btn-delete').click();
  await expect(page.locator('.contact-list-name', { hasText: `${name} Test` })).toHaveCount(0);
});

test('edit an existing contact', async ({ page }) => {
  const name = `Edit-${Date.now()}`;
  await page.getByRole('button', { name: '+ New Contact' }).click();
  await page.locator('input.field-input[placeholder="First name"]').fill(name);
  await page.locator('input.field-input[placeholder="Last name"]').fill('Before');
  await page.locator('input.field-input[placeholder="Email address"]').fill(`${name}@test.com`);
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.locator('.contact-list-name', { hasText: `${name} Before` })).toBeVisible();

  await page.locator('.contact-list-item', { hasText: `${name} Before` }).click();
  await page.getByRole('button', { name: 'Edit' }).click();
  await page.locator('input.field-input[placeholder="Last name"]').fill('After');
  await page.getByRole('button', { name: 'Save' }).click();

  await expect(page.locator('.contact-list-name', { hasText: `${name} After` })).toBeVisible();

  // cleanup
  await page.locator('.contact-list-item', { hasText: `${name} After` }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.locator('.dialog .btn-delete').click();
});

test('contact detail shows email', async ({ page }) => {
  const name = `Detail-${Date.now()}`;
  await page.getByRole('button', { name: '+ New Contact' }).click();
  await page.locator('input.field-input[placeholder="First name"]').fill(name);
  await page.locator('input.field-input[placeholder="Last name"]').fill('Check');
  await page.locator('input.field-input[placeholder="Email address"]').fill(`${name}@test.com`);
  await page.getByRole('button', { name: 'Create' }).click();

  await page.locator('.contact-list-item', { hasText: `${name} Check` }).click();
  await expect(page.locator('.detail-value', { hasText: `${name}@test.com` })).toBeVisible();

  // cleanup
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.locator('.dialog .btn-delete').click();
});
