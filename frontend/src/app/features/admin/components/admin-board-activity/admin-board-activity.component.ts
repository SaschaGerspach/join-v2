import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { AdminApiService, AdminBoardsResponse } from '../../../../core/admin/admin-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-admin-board-activity',
  standalone: true,
  imports: [TranslateModule, DatePipe, LoadingSpinnerComponent],
  templateUrl: './admin-board-activity.component.html',
  styleUrl: './admin-board-activity.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminBoardActivityComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  data = signal<AdminBoardsResponse | null>(null);
  loading = signal(true);

  ngOnInit(): void {
    this.api.getBoards()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: d => { this.data.set(d); this.loading.set(false); },
        error: () => { this.toast.show(this.translate.instant('TOAST.GENERIC_ERROR'), 'error'); this.loading.set(false); },
      });
  }
}
