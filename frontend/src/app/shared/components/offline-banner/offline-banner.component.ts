import { ChangeDetectionStrategy, Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { OfflineQueueService } from '../../../core/offline/offline-queue.service';

@Component({
  selector: 'app-offline-banner',
  standalone: true,
  template: `
    @if (offline()) {
      <div class="offline-banner">
        You are offline — changes will sync automatically when reconnected.
        @if (queue.pendingCount > 0) {
          <span class="queue-count">({{ queue.pendingCount }} pending)</span>
        }
      </div>
    }
  `,
  styles: [`
    .offline-banner {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 8px 16px;
      background: #dc2626;
      color: #fff;
      text-align: center;
      font-size: 0.85rem;
      font-weight: 500;
      z-index: 9999;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OfflineBannerComponent implements OnInit, OnDestroy {
  readonly queue = inject(OfflineQueueService);
  offline = signal(!navigator.onLine);

  private onOnline = () => this.offline.set(false);
  private onOffline = () => this.offline.set(true);

  ngOnInit(): void {
    window.addEventListener('online', this.onOnline);
    window.addEventListener('offline', this.onOffline);
  }

  ngOnDestroy(): void {
    window.removeEventListener('online', this.onOnline);
    window.removeEventListener('offline', this.onOffline);
  }
}
