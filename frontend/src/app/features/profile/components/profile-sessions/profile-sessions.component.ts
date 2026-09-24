import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { AuthApiService, Session } from '../../../../core/auth/auth-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-profile-sessions',
  imports: [DatePipe, TranslateModule],
  templateUrl: './profile-sessions.component.html',
  styleUrl: './profile-sessions.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfileSessionsComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  sessions = signal<Session[]>([]);

  ngOnInit(): void {
    this.authApi.getSessions().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: sessions => this.sessions.set(sessions),
    });
  }

  revokeSession(id: number): void {
    this.authApi.revokeSession(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.sessions.update(list => list.filter(s => s.id !== id));
        this.toast.show(this.translate.instant('TOAST.SESSION_REVOKED'));
      },
    });
  }

  revokeAllSessions(): void {
    this.authApi.revokeAllSessions().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.sessions.update(list => list.filter(s => s.is_current));
        this.toast.show(this.translate.instant('TOAST.ALL_SESSIONS_REVOKED'));
      },
    });
  }
}
