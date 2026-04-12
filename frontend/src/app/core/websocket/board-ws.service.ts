import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';

export type BoardWsEvent = {
  event: string;
  data: any;
};

@Injectable({ providedIn: 'root' })
export class BoardWsService {
  private ws: WebSocket | null = null;
  readonly events$ = new Subject<BoardWsEvent>();

  connect(boardId: number): void {
    this.disconnect();
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const host = new URL(environment.apiUrl).host;
    this.ws = new WebSocket(`${protocol}://${host}/ws/board/${boardId}/`);

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
