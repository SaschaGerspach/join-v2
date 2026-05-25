import { Injectable, inject, signal, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { TranslateService } from '@ngx-translate/core';
import { ToastService } from '../../shared/services/toast.service';
import { getAllQueued, putQueued, deleteQueued, QueuedRequest } from './offline-db';

const MAX_AGE_MS = 24 * 60 * 60 * 1000;
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000];

@Injectable({ providedIn: 'root' })
export class OfflineQueueService implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly onOnline = () => this.flush();

  readonly pendingCount = signal(0);

  constructor() {
    window.addEventListener('online', this.onOnline);
    this.refreshCount();
  }

  ngOnDestroy(): void {
    window.removeEventListener('online', this.onOnline);
  }

  async enqueue(method: string, url: string, body: unknown): Promise<void> {
    const all = await getAllQueued();
    const existing = all.find(r => r.method === method && r.url === url);
    if (existing?.id != null) {
      await putQueued({ ...existing, body, timestamp: Date.now() });
    } else {
      await putQueued({ method, url, body, timestamp: Date.now() });
    }
    this.refreshCount();
  }

  async flush(): Promise<void> {
    const queue = await getAllQueued();
    if (queue.length === 0) return;

    const now = Date.now();
    let success = 0;
    let failed = 0;

    for (const req of queue) {
      if (now - req.timestamp > MAX_AGE_MS) {
        if (req.id != null) await deleteQueued(req.id);
        continue;
      }

      const ok = await this.sendWithRetry(req);
      if (ok) {
        success++;
      } else {
        failed++;
      }
      if (req.id != null) await deleteQueued(req.id);
      this.refreshCount();
    }

    if (success > 0) this.toast.show(this.translate.instant('TOAST.QUEUED_CHANGES_SYNCED', { count: success }));
    if (failed > 0) this.toast.show(this.translate.instant('TOAST.QUEUED_CHANGES_FAILED', { count: failed }), 'error');
  }

  private sendWithRetry(req: QueuedRequest): Promise<boolean> {
    return new Promise(resolve => {
      const attempt = (retryIndex: number) => {
        this.http.request(req.method, req.url, { body: req.body, withCredentials: true }).subscribe({
          next: () => resolve(true),
          error: () => {
            if (retryIndex < MAX_RETRIES - 1) {
              setTimeout(() => attempt(retryIndex + 1), RETRY_DELAYS[retryIndex]);
            } else {
              resolve(false);
            }
          },
        });
      };
      attempt(0);
    });
  }

  private async refreshCount(): Promise<void> {
    try {
      const all = await getAllQueued();
      this.pendingCount.set(all.length);
    } catch {
      this.pendingCount.set(0);
    }
  }
}
