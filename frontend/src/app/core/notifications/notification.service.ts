import { Injectable, computed, inject, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from '../auth/auth.service';
import { environment } from '../../../environments/environment';
import { AppNotification, NotificationsApiService } from './notifications-api.service';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly api = inject(NotificationsApiService);
  private readonly auth = inject(AuthService);

  private ws: WebSocket | null = null;
  private intentionalClose = false;
  private reconnectDelay = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  readonly notifications = signal<AppNotification[]>([]);
  readonly unreadCount = computed(() => this.notifications().filter(n => !n.is_read).length);
  readonly newNotification$ = new Subject<AppNotification>();

  connect(): void {
    this.disconnect();
    this.intentionalClose = false;
    this.reconnectDelay = 1000;
    this.loadNotifications();
    this.openSocket();
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.clearReconnectTimer();
    this.ws?.close();
    this.ws = null;
  }

  markAsRead(id: number): void {
    this.api.markAsRead(id).subscribe({
      next: updated => this.notifications.update(list => list.map(n => n.id === id ? updated : n)),
      error: () => {},
    });
  }

  markAllAsRead(): void {
    this.api.markAllAsRead().subscribe({
      next: () => this.notifications.update(list => list.map(n => ({ ...n, is_read: true }))),
      error: () => {},
    });
  }

  private loadNotifications(): void {
    this.api.getAll().subscribe({
      next: list => this.notifications.set(list),
      error: () => {},
    });
  }

  private openSocket(): void {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const host = new URL(environment.apiUrl).host;
    this.ws = new WebSocket(`${protocol}://${host}/ws/notifications/`);

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
        const parsed = JSON.parse(msg.data);
        if (parsed.event === 'new_notification') {
          const notification: AppNotification = parsed.data;
          this.notifications.update(list => [notification, ...list]);
          this.newNotification$.next(notification);
        }
      } catch { /* ignore parse errors */ }
    };

    this.ws.onclose = () => {
      this.ws = null;
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.intentionalClose) {
        this.openSocket();
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
