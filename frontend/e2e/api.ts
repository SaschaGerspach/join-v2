import { APIRequestContext, request as pwRequest } from '@playwright/test';
import { TEST_USER } from './global-setup';

const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';

async function getAccessToken(): Promise<string> {
  const ctx = await pwRequest.newContext({ baseURL: API_URL });
  const res = await ctx.post('/auth/login', {
    data: { email: TEST_USER.email, password: TEST_USER.password },
  });
  if (!res.ok()) {
    throw new Error(`Login failed: ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  await ctx.dispose();
  return body.access;
}

async function apiContext(): Promise<APIRequestContext> {
  const token = await getAccessToken();
  return pwRequest.newContext({
    baseURL: API_URL,
    extraHTTPHeaders: { Authorization: `Bearer ${token}` },
  });
}

export async function createBoard(title: string): Promise<{ id: number; title: string }> {
  const ctx = await apiContext();
  const res = await ctx.post('/boards/', { data: { title } });
  if (!res.ok()) throw new Error(`createBoard failed: ${res.status()} ${await res.text()}`);
  const board = await res.json();
  await ctx.dispose();
  return board;
}

export async function deleteBoard(id: number): Promise<void> {
  const ctx = await apiContext();
  await ctx.delete(`/boards/${id}/`);
  await ctx.dispose();
}

export async function createColumn(boardId: number, title: string): Promise<{ id: number }> {
  const ctx = await apiContext();
  const res = await ctx.post(`/columns/?board=${boardId}`, { data: { title } });
  if (!res.ok()) throw new Error(`createColumn failed: ${res.status()} ${await res.text()}`);
  const column = await res.json();
  await ctx.dispose();
  return column;
}
