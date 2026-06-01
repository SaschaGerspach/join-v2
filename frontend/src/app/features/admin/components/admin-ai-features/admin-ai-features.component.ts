import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule } from '@ngx-translate/core';
import { AdminApiService, AiFeature } from '../../../../core/admin/admin-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-admin-ai-features',
  standalone: true,
  imports: [TranslateModule, LoadingSpinnerComponent],
  templateUrl: './admin-ai-features.component.html',
  styleUrl: './admin-ai-features.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminAiFeaturesComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly destroyRef = inject(DestroyRef);

  features = signal<AiFeature[]>([]);
  provider = signal('');
  configured = signal(false);
  loading = signal(true);
  pending = signal<Set<string>>(new Set());

  ngOnInit(): void {
    this.api.getAiFeatures()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: list => {
          this.features.set(list.features);
          this.provider.set(list.provider);
          this.configured.set(list.configured);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  isPending(key: string): boolean {
    return this.pending().has(key);
  }

  toggle(feature: AiFeature): void {
    if (this.isPending(feature.key)) return;
    this.pending.update(set => new Set(set).add(feature.key));
    this.api.setAiFeature(feature.key, !feature.enabled)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: list => {
          this.features.set(list.features);
          this.configured.set(list.configured);
          this.clearPending(feature.key);
        },
        error: () => this.clearPending(feature.key),
      });
  }

  private clearPending(key: string): void {
    this.pending.update(set => {
      const next = new Set(set);
      next.delete(key);
      return next;
    });
  }
}
