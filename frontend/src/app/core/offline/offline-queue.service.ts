import { Injectable, inject, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ToastService } from '../../shared/services/toast.service';

type QueuedRequest = {
  method: string;
  url: string;
  body: unknown;
  timestamp: number;
};

const STORAGE_KEY = 'offline_queue';

@Injectable({ providedIn: 'root' })
export class OfflineQueueService implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly toast = inject(ToastService);
  private readonly onOnline = () => this.flush();

  constructor() {
    window.addEventListener('online', this.onOnline);
  }

  ngOnDestroy(): void {
    window.removeEventListener('online', this.onOnline);
  }

  enqueue(method: string, url: string, body: unknown): void {
    const queue = this.getQueue();
    queue.push({ method, url, body, timestamp: Date.now() });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  }

  get pendingCount(): number {
    return this.getQueue().length;
  }

  flush(): void {
    const queue = this.getQueue();
    if (queue.length === 0) return;

    localStorage.removeItem(STORAGE_KEY);
    let success = 0;
    let failed = 0;

    const processNext = (index: number) => {
      if (index >= queue.length) {
        if (success > 0) this.toast.show(`${success} queued change(s) synced.`);
        if (failed > 0) this.toast.show(`${failed} queued change(s) failed.`, 'error');
        return;
      }
      const req = queue[index];
      const obs = this.http.request(req.method, req.url, { body: req.body, withCredentials: true });
      obs.subscribe({
        next: () => { success++; processNext(index + 1); },
        error: () => { failed++; processNext(index + 1); },
      });
    };

    processNext(0);
  }

  private getQueue(): QueuedRequest[] {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  }
}
