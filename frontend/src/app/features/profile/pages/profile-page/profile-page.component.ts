import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import { AuthApiService, Session, TotpSetupResponse } from '../../../../core/auth/auth-api.service';
import { UsersApiService } from '../../../../core/users/users-api.service';
import { NotificationsApiService } from '../../../../core/notifications/notifications-api.service';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { UserAvatarComponent } from '../../../../shared/components/user-avatar/user-avatar.component';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [FormsModule, ConfirmDialogComponent, LoadingSpinnerComponent, DatePipe, UserAvatarComponent, TranslateModule],
  templateUrl: './profile-page.component.html',
  styleUrl: './profile-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfilePageComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly authApi = inject(AuthApiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly usersApi = inject(UsersApiService);
  private readonly notificationsApi = inject(NotificationsApiService);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  loading = signal(true);
  firstName = signal('');
  lastName = signal('');
  email = signal('');
  newPassword = signal('');
  confirmPassword = signal('');

  saving = signal(false);
  errorMessage = signal('');
  showDeleteConfirm = signal(false);

  boards = signal<Board[]>([]);
  sessions = signal<Session[]>([]);
  disabledTypes = signal<Set<string>>(new Set());
  mutedBoardIds = signal<Set<number>>(new Set());
  emailDelivery = signal<'instant' | 'digest' | 'none'>('instant');

  avatarUrl = signal<string | null>(null);

  totpEnabled = signal(false);
  totpSetup = signal<TotpSetupResponse | null>(null);
  totpConfirmCode = signal('');
  totpDisableCode = signal('');
  totpDisablePassword = signal('');
  totpError = signal('');

  initials = computed(() => {
    const f = this.firstName()[0] ?? '';
    const l = this.lastName()[0] ?? '';
    return (f + l).toUpperCase() || (this.email()[0]?.toUpperCase() ?? '?');
  });

  private userId = 0;

  ngOnInit(): void {
    const user = this.auth.user();
    if (!user) return;
    this.userId = user.id;

    this.totpEnabled.set(user.totp_enabled ?? false);
    this.avatarUrl.set(user.avatar_url ?? null);

    this.usersApi.get(this.userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (profile) => {
        this.firstName.set(profile.first_name);
        this.lastName.set(profile.last_name);
        this.email.set(profile.email);
        this.loading.set(false);
      },
      error: () => { this.toast.show('Failed to load profile.', 'error'); this.loading.set(false); },
    });

    this.notificationsApi.getPreferences().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: prefs => {
        this.disabledTypes.set(new Set(prefs.disabled_types));
        this.mutedBoardIds.set(new Set(prefs.muted_boards));
        this.emailDelivery.set(prefs.email_delivery);
      },
      error: () => {},
    });

    this.boardsApi.getAll().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: boards => this.boards.set(boards),
      error: () => {},
    });

    this.loadSessions();
  }

  loadSessions(): void {
    this.authApi.getSessions().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: sessions => this.sessions.set(sessions),
      error: () => {},
    });
  }

  revokeSession(id: number): void {
    this.authApi.revokeSession(id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.sessions.update(list => list.filter(s => s.id !== id));
        this.toast.show('Session revoked.');
      },
      error: () => this.toast.show('Failed to revoke session.', 'error'),
    });
  }

  revokeAllSessions(): void {
    this.authApi.revokeAllSessions().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.sessions.update(list => list.filter(s => s.is_current));
        this.toast.show('All other sessions revoked.');
      },
      error: () => this.toast.show('Failed to revoke sessions.', 'error'),
    });
  }

  exportData(): void {
    this.usersApi.exportData().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: data => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'my-data-export.json';
        a.click();
        URL.revokeObjectURL(url);
        this.toast.show('Data exported.');
      },
      error: () => this.toast.show('Failed to export data.', 'error'),
    });
  }

  save(): void {
    this.errorMessage.set('');

    const pw = this.newPassword().trim();
    const confirm = this.confirmPassword().trim();

    if (pw && pw.length < 8) {
      this.errorMessage.set('Password must be at least 8 characters.');
      return;
    }
    if (pw && pw !== confirm) {
      this.errorMessage.set('Passwords do not match.');
      return;
    }

    const payload: Record<string, string> = {
      first_name: this.firstName().trim(),
      last_name: this.lastName().trim(),
      email: this.email().trim(),
    };

    if (pw) payload['password'] = pw;

    this.saving.set(true);
    this.usersApi.patch(this.userId, payload).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.newPassword.set('');
        this.confirmPassword.set('');
        this.saving.set(false);
        this.toast.show('Profile updated successfully.');
      },
      error: (err) => {
        this.errorMessage.set(err?.error?.detail ?? 'Something went wrong.');
        this.saving.set(false);
      },
    });
  }

  confirmDeleteAccount(): void {
    this.usersApi.delete(this.userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.auth.clearUser();
        this.router.navigate(['/login']);
      },
      error: () => this.toast.show('Failed to delete account.', 'error'),
    });
  }

  toggleType(type: string): void {
    const types = new Set(this.disabledTypes());
    if (types.has(type)) {
      types.delete(type);
    } else {
      types.add(type);
    }
    this.disabledTypes.set(types);
    this.savePreferences();
  }

  setEmailDelivery(value: 'instant' | 'digest' | 'none'): void {
    this.emailDelivery.set(value);
    this.savePreferences();
  }

  toggleMuteBoard(boardId: number): void {
    const muted = new Set(this.mutedBoardIds());
    if (muted.has(boardId)) {
      muted.delete(boardId);
    } else {
      muted.add(boardId);
    }
    this.mutedBoardIds.set(muted);
    this.savePreferences();
  }

  startTotpSetup(): void {
    this.totpError.set('');
    this.authApi.totpSetup().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (res) => this.totpSetup.set(res),
      error: () => this.toast.show('Failed to start 2FA setup.', 'error'),
    });
  }

  confirmTotp(): void {
    const code = this.totpConfirmCode().trim();
    if (code.length !== 6) { this.totpError.set('Enter a 6-digit code.'); return; }
    this.totpError.set('');
    this.authApi.totpConfirm(code).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.totpEnabled.set(true);
        this.totpSetup.set(null);
        this.totpConfirmCode.set('');
        this.toast.show('2FA enabled.');
      },
      error: () => this.totpError.set('Invalid code. Try again.'),
    });
  }

  cancelTotpSetup(): void {
    this.totpSetup.set(null);
    this.totpConfirmCode.set('');
    this.totpError.set('');
  }

  disableTotp(): void {
    const code = this.totpDisableCode().trim();
    const password = this.totpDisablePassword().trim();
    if (!password) { this.totpError.set('Password is required.'); return; }
    if (code.length !== 6) { this.totpError.set('Enter a 6-digit code.'); return; }
    this.totpError.set('');
    this.authApi.totpDisable(password, code).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.totpEnabled.set(false);
        this.totpDisableCode.set('');
        this.totpDisablePassword.set('');
        this.toast.show('2FA disabled.');
      },
      error: (err) => this.totpError.set(err?.error?.detail ?? 'Failed to disable 2FA.'),
    });
  }

  onAvatarSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.authApi.uploadAvatar(file).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: res => {
        this.avatarUrl.set(res.avatar_url);
        this.auth.init();
        this.toast.show('Avatar updated.');
      },
      error: (err) => this.toast.show(err?.error?.detail ?? 'Failed to upload avatar.', 'error'),
    });
  }

  removeAvatar(): void {
    this.authApi.deleteAvatar().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.avatarUrl.set(null);
        this.auth.init();
        this.toast.show('Avatar removed.');
      },
      error: () => this.toast.show('Failed to remove avatar.', 'error'),
    });
  }

  private savePreferences(): void {
    this.notificationsApi.updatePreferences({
      disabled_types: [...this.disabledTypes()],
      muted_boards: [...this.mutedBoardIds()],
      email_delivery: this.emailDelivery(),
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      error: () => this.toast.show('Failed to save notification settings.', 'error'),
    });
  }
}
