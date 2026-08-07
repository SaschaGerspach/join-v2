import { Injectable, inject, signal } from '@angular/core';
import { Subject, take } from 'rxjs';
import { Column } from '../columns/columns-api.service';
import { Task } from '../tasks/tasks-api.service';
import { environment } from '../../../environments/environment';
import { AuthService } from '../auth/auth.service';

export type PresenceUser = { id: number; first_name: string; last_name: string; email: string; avatar_url: string | null };

export type AutomationExecuted = { rule_name: string; task_id: number; actions: string[] };

export type BoardWsEvent =
  | { event: 'task_created'; data: Task }
  | { event: 'task_updated'; data: Task }
  | { event: 'task_deleted'; data: { id: number } }
  | { event: 'tasks_reordered'; data: Task[] }
  | { event: 'column_created'; data: Column }
  | { event: 'column_updated'; data: Column }
  | { event: 'column_deleted'; data: { id: number } }
  | { event: 'columns_reordered'; data: Column[] }
  | { event: 'automation_executed'; data: AutomationExecuted }
  | { event: 'presence_list'; data: PresenceUser[] }
  | { event: 'presence_joined'; data: PresenceUser }
  | { event: 'presence_left'; data: { id: number } };

const BOARD_WS_EVENTS = new Set<string>([
  'task_created', 'task_updated', 'task_deleted', 'tasks_reordered',
  'column_created', 'column_updated', 'column_deleted', 'columns_reordered',
  'automation_executed',
  'presence_list', 'presence_joined', 'presence_left',
]);

export type ConnectionStatus = 'connected' | 'reconnecting' | 'offline';

// The consumer acknowledges a successful authenticate with this frame once the
// socket has been added to the board group (boards_api/consumers.py).
function isAuthenticatedAck(value: unknown): boolean {
  return typeof value === 'object' && value !== null
    && (value as Record<string, unknown>)['type'] === 'authenticated';
}

export function isBoardWsEvent(value: unknown): value is BoardWsEvent {
  return typeof value === 'object' && value !== null
    && 'event' in value && typeof (value as Record<string, unknown>)['event'] === 'string'
    && BOARD_WS_EVENTS.has((value as Record<string, unknown>)['event'] as string)
    && 'data' in value;
}

@Injectable({ providedIn: 'root' })
export class BoardWsService {
  private readonly auth = inject(AuthService);
  private ws: WebSocket | null = null;
  private boardId: number | null = null;
  private intentionalClose = false;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private authenticatedOnce = false;
  readonly events$ = new Subject<BoardWsEvent>();
  // Fires after a re-authentication on a reconnected socket. Events sent while
  // the socket was down are gone, so consumers refetch instead of catching up.
  readonly resync$ = new Subject<void>();

  private readonly _status = signal<ConnectionStatus>('offline');
  readonly status = this._status.asReadonly();

  connect(boardId: number): void {
    this.disconnect();
    this.boardId = boardId;
    this.intentionalClose = false;
    this.reconnectDelay = 1000;
    this.authenticatedOnce = false;
    this._status.set('reconnecting');
    this.openSocket(boardId);
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.boardId = null;
    this.clearReconnectTimer();
    this.ws?.close();
    this.ws = null;
    this._status.set('offline');
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
        const parsed: unknown = JSON.parse(msg.data);
        if (isAuthenticatedAck(parsed)) {
          this.onAuthenticated();
        } else if (isBoardWsEvent(parsed)) {
          this.events$.next(parsed);
        } else {
          console.warn('WebSocket: discarded unknown board event', parsed);
        }
      } catch (e) {
        console.error('WebSocket: failed to parse message', e);
      }
    };

    this.ws.onclose = () => {
      this.ws = null;
      if (!this.intentionalClose && this.boardId !== null) {
        this._status.set(navigator.onLine ? 'reconnecting' : 'offline');
        this.scheduleReconnect();
      } else {
        this._status.set('offline');
      }
    };
  }

  private onAuthenticated(): void {
    this._status.set('connected');
    if (this.authenticatedOnce) {
      this.resync$.next();
    } else {
      this.authenticatedOnce = true;
    }
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    const id = this.boardId;
    if (id === null) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.boardId === id && !this.intentionalClose) {
        this.reopenWithValidToken(id);
      }
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  // A stale token would just get the socket closed with 4401 and spin the
  // backoff, so renew it before reconnecting rather than after failing.
  private reopenWithValidToken(id: number): void {
    if (!this.auth.isAccessTokenExpiring()) {
      this.openSocket(id);
      return;
    }
    this.auth.refreshAccessToken().pipe(take(1)).subscribe({
      next: () => {
        if (this.boardId === id && !this.intentionalClose) this.openSocket(id);
      },
      error: () => {
        if (this.boardId === id && !this.intentionalClose) this.scheduleReconnect();
      },
    });
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
