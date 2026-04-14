import { Component, inject, signal, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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
  imports: [LoadingSpinnerComponent],
  templateUrl: './admin-page.component.html',
  styleUrl: './admin-page.component.scss',
})
export class AdminPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly toast = inject(ToastService);

  stats = signal<AdminStats | null>(null);
  loading = signal(true);

  readonly djangoAdminUrl = `${environment.apiUrl}/manage/`;

  ngOnInit(): void {
    this.http
      .get<AdminStats>(`${environment.apiUrl}/admin-api/stats/`, { withCredentials: true })
      .subscribe({
        next: s => { this.stats.set(s); this.loading.set(false); },
        error: () => { this.toast.show('Failed to load stats.', 'error'); this.loading.set(false); },
      });
  }
}
