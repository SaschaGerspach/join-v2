import { request, FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';
const TEST_USER = {
  email: 'e2e@example.com',
  password: 'E2ePass123!',
  first_name: 'E2E',
  last_name: 'User',
};

export default async function globalSetup(_config: FullConfig): Promise<void> {
  const storageDir = path.resolve(__dirname, '.auth');
  const storagePath = path.join(storageDir, 'user.json');
  fs.mkdirSync(storageDir, { recursive: true });

  const ctx = await request.newContext({ baseURL: API_URL });

  const register = await ctx.post('/auth/register', { data: TEST_USER });
  if (!register.ok() && register.status() !== 400) {
    throw new Error(`Registration failed: ${register.status()} ${await register.text()}`);
  }

  const login = await ctx.post('/auth/login', {
    data: { email: TEST_USER.email, password: TEST_USER.password },
  });
  if (!login.ok()) {
    throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
  }

  await ctx.storageState({ path: storagePath });
  await ctx.dispose();
}

export { TEST_USER };
