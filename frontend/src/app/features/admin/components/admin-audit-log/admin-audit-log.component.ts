import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { AdminApiService, AuditLogEntry } from '../../../../core/admin/admin-api.service';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-admin-audit-log',
  standalone: true,
  imports: [TranslateModule, FormsModule, DatePipe, LoadingSpinnerComponent],
  templateUrl: './admin-audit-log.component.html',
  styleUrl: './admin-audit-log.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminAuditLogComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  entries = signal<AuditLogEntry[]>([]);
  eventTypes = signal<string[]>([]);
  selectedType = signal('');
  loading = signal(true);

  ngOnInit(): void {
    this.load();
  }

  onFilterChange(value: string): void {
    this.selectedType.set(value);
    this.load();
  }

  private load(): void {
    this.loading.set(true);
    const type = this.selectedType() || undefined;
    this.api.getAuditLog(type)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.entries.set(res.results);
          this.eventTypes.set(res.event_types);
          this.loading.set(false);
        },
        error: () => {
          this.toast.show(this.translate.instant('TOAST.GENERIC_ERROR'), 'error');
          this.loading.set(false);
        },
      });
  }
}
