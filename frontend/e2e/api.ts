import { APIRequestContext, request as pwRequest } from '@playwright/test';

const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';

async function getAccessToken(): Promise<string> {
  const ctx = await pwRequest.newContext({
    baseURL: API_URL,
    storageState: 'e2e/.auth/user.json',
  });
  const res = await ctx.post('/auth/token/refresh', { data: {} });
  if (!res.ok()) {
    throw new Error(`Token refresh failed: ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  await ctx.dispose();
  return body.access;
}

export async function apiContext(): Promise<APIRequestContext> {
  const token = await getAccessToken();
  return pwRequest.newContext({
    baseURL: API_URL,
    extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    storageState: 'e2e/.auth/user.json',
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
