import { ChangeDetectionStrategy, Component, inject, signal, OnInit, DestroyRef } from '@angular/core';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-sw-update-banner',
  standalone: true,
  imports: [TranslateModule],
  template: `
    @if (updateAvailable()) {
      <div class="update-banner" role="alert">
        <span>{{ 'SW_UPDATE.AVAILABLE' | translate }}</span>
        <button class="update-btn" (click)="reload()">{{ 'SW_UPDATE.RELOAD' | translate }}</button>
      </div>
    }
  `,
  styles: [`
    .update-banner {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 10px 16px;
      background: #1565c0;
      color: #fff;
      text-align: center;
      font-size: 0.85rem;
      font-weight: 500;
      z-index: 9998;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
    }
    .update-btn {
      background: #fff;
      color: #1565c0;
      border: none;
      border-radius: 6px;
      padding: 4px 14px;
      font-weight: 700;
      font-size: 0.82rem;
      cursor: pointer;
    }
    .update-btn:hover { opacity: 0.9; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SwUpdateBannerComponent implements OnInit {
  private readonly swUpdate = inject(SwUpdate);
  private readonly destroyRef = inject(DestroyRef);

  updateAvailable = signal(false);

  ngOnInit(): void {
    if (!this.swUpdate.isEnabled) return;

    this.swUpdate.versionUpdates
      .pipe(
        filter((e): e is VersionReadyEvent => e.type === 'VERSION_READY'),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => this.updateAvailable.set(true));
  }

  reload(): void {
    this.swUpdate.activateUpdate().then(() => document.location.reload());
  }
}
