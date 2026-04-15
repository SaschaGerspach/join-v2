import { Injectable, inject } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from '../auth/auth.service';

export type BoardWsEvent = {
  event: string;
  data: any;
};

@Injectable({ providedIn: 'root' })
export class BoardWsService {
  private readonly auth = inject(AuthService);
  private ws: WebSocket | null = null;
  readonly events$ = new Subject<BoardWsEvent>();

  connect(boardId: number): void {
    this.disconnect();
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const host = new URL(environment.apiUrl).host;
    const token = this.auth.getAccessToken();
    const query = token ? `?token=${encodeURIComponent(token)}` : '';
    this.ws = new WebSocket(`${protocol}://${host}/ws/board/${boardId}/${query}`);

    this.ws.onmessage = (msg) => {
      try {
        this.events$.next(JSON.parse(msg.data));
      } catch {}
    };

    this.ws.onclose = () => {
      this.ws = null;
    };
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}
