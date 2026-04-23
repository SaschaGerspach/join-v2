import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { HttpClient } from '@angular/common/http';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { environment } from '../../../../../environments/environment';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ToastService } from '../../../../shared/services/toast.service';

type AdminStats = {
  users: number;
  boards: number;
  tasks: number;
  contacts: number;
};

@Component({
  selector: 'app-admin-page',
  standalone: true,
  imports: [LoadingSpinnerComponent, TranslateModule],
  templateUrl: './admin-page.component.html',
  styleUrl: './admin-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  stats = signal<AdminStats | null>(null);
  loading = signal(true);

  readonly djangoAdminUrl = `${environment.apiUrl}/manage/`;

  ngOnInit(): void {
    this.http
      .get<AdminStats>(`${environment.apiUrl}/admin-api/stats/`, { withCredentials: true })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: s => { this.stats.set(s); this.loading.set(false); },
        error: () => { this.toast.show(this.translate.instant('TOAST.FAILED_LOAD_STATS'), 'error'); this.loading.set(false); },
      });
  }
}
