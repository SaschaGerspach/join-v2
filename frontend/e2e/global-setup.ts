import { request, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import * as path from 'path';

const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';
const TEST_USER = {
  email: 'e2e@example.com',
  password: 'E2ePass123!',
  first_name: 'E2E',
  last_name: 'User',
};

export default async function globalSetup(_config: FullConfig): Promise<void> {
  const ctx = await request.newContext({ baseURL: API_URL });

  const register = await ctx.post('/auth/register', { data: TEST_USER });
  if (!register.ok() && register.status() !== 400) {
    throw new Error(`Registration failed: ${register.status()} ${await register.text()}`);
  }

  verifyUserInBackend(TEST_USER.email);
  await ctx.dispose();
}

function verifyUserInBackend(email: string): void {
  const backendDir = path.resolve(__dirname, '..', '..', 'backend');
  const python = process.env.E2E_PYTHON ?? 'python';
  const code = `from auth_api.models import User; User.objects.filter(email='${email}').update(is_verified=True)`;
  execSync(`${python} manage.py shell -c "${code}"`, {
    cwd: backendDir,
    env: {
      ...process.env,
      DJANGO_SECRET_KEY: process.env.DJANGO_SECRET_KEY ?? 'dev-test',
      DJANGO_DEBUG: process.env.DJANGO_DEBUG ?? 'true',
    },
    stdio: 'inherit',
  });
}

export { TEST_USER };
