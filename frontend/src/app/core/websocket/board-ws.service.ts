import { Injectable, inject } from '@angular/core';
import { Subject } from 'rxjs';
import { Column } from '../columns/columns-api.service';
import { Task } from '../tasks/tasks-api.service';
import { environment } from '../../../environments/environment';
import { AuthService } from '../auth/auth.service';

export type PresenceUser = { id: number; first_name: string; last_name: string; email: string; avatar_url: string | null };

export type BoardWsEvent =
  | { event: 'task_created'; data: Task }
  | { event: 'task_updated'; data: Task }
  | { event: 'task_deleted'; data: { id: number } }
  | { event: 'tasks_reordered'; data: Task[] }
  | { event: 'column_created'; data: Column }
  | { event: 'column_updated'; data: Column }
  | { event: 'column_deleted'; data: { id: number } }
  | { event: 'presence_list'; data: PresenceUser[] }
  | { event: 'presence_joined'; data: PresenceUser }
  | { event: 'presence_left'; data: { id: number } };

@Injectable({ providedIn: 'root' })
export class BoardWsService {
  private readonly auth = inject(AuthService);
  private ws: WebSocket | null = null;
  private boardId: number | null = null;
  private intentionalClose = false;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  readonly events$ = new Subject<BoardWsEvent>();

  connect(boardId: number): void {
    this.disconnect();
    this.boardId = boardId;
    this.intentionalClose = false;
    this.reconnectDelay = 1000;
    this.openSocket(boardId);
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.boardId = null;
    this.clearReconnectTimer();
    this.ws?.close();
    this.ws = null;
  }

  private openSocket(boardId: number): void {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const host = new URL(environment.apiUrl).host;
    this.ws = new WebSocket(`${protocol}://${host}/ws/board/${boardId}/`);

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      const token = this.auth.getAccessToken();
      if (token) {
        this.ws?.send(JSON.stringify({ type: 'authenticate', token }));
      } else {
        this.ws?.close();
      }
    };

    this.ws.onmessage = (msg) => {
      try {
        this.events$.next(JSON.parse(msg.data));
      } catch (e) {
        console.error('WebSocket: failed to parse message', e);
      }
    };

    this.ws.onclose = () => {
      this.ws = null;
      if (!this.intentionalClose && this.boardId !== null) {
        this.scheduleReconnect();
      }
    };
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    const id = this.boardId;
    if (id === null) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.boardId === id && !this.intentionalClose) {
        this.openSocket(id);
      }
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
