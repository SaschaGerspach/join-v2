import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { AdminApiService, AdminStats } from '../../../../core/admin/admin-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-admin-stats',
  standalone: true,
  imports: [TranslateModule, LoadingSpinnerComponent],
  templateUrl: './admin-stats.component.html',
  styleUrl: './admin-stats.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminStatsComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  stats = signal<AdminStats | null>(null);
  loading = signal(true);
  expandedCard = signal<string | null>(null);

  ngOnInit(): void {
    this.api.getStats()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: s => { this.stats.set(s); this.loading.set(false); },
        error: () => { this.toast.show(this.translate.instant('TOAST.FAILED_LOAD_STATS'), 'error'); this.loading.set(false); },
      });
  }

  toggleCard(key: string): void {
    this.expandedCard.set(this.expandedCard() === key ? null : key);
  }
}
