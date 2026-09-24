import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { UsersApiService } from '../../../../core/users/users-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { UserAvatarComponent } from '../../../../shared/components/user-avatar/user-avatar.component';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ProfileNotificationsComponent } from '../../components/profile-notifications/profile-notifications.component';
import { ProfileSessionsComponent } from '../../components/profile-sessions/profile-sessions.component';
import { ProfileTwoFactorComponent } from '../../components/profile-two-factor/profile-two-factor.component';

@Component({
  selector: 'app-profile-page',
  imports: [
    FormsModule,
    ConfirmDialogComponent,
    LoadingSpinnerComponent,
    UserAvatarComponent,
    TranslateModule,
    ProfileNotificationsComponent,
    ProfileSessionsComponent,
    ProfileTwoFactorComponent,
  ],
  templateUrl: './profile-page.component.html',
  styleUrl: './profile-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfilePageComponent implements OnInit {
  readonly auth = inject(AuthService);
  private readonly authApi = inject(AuthApiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly usersApi = inject(UsersApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);

  loading = signal(true);
  firstName = signal('');
  lastName = signal('');
  email = signal('');
  currentPassword = signal('');
  newPassword = signal('');
  confirmPassword = signal('');

  saving = signal(false);
  errorMessage = signal('');
  showDeleteConfirm = signal(false);

  avatarUrl = signal<string | null>(null);

  isAdmin = computed(() => this.auth.user()?.is_staff ?? false);

  private userId = 0;

  ngOnInit(): void {
    const user = this.auth.user();
    if (!user) return;
    this.userId = user.id;

    this.avatarUrl.set(user.avatar_url ?? null);

    this.usersApi.get(this.userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (profile) => {
        this.firstName.set(profile.first_name);
        this.lastName.set(profile.last_name);
        this.email.set(profile.email);
        this.loading.set(false);
      },
      error: () => { this.loading.set(false); },
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
        this.toast.show(this.translate.instant('TOAST.DATA_EXPORTED'));
      },
    });
  }

  save(): void {
    this.errorMessage.set('');

    const pw = this.newPassword().trim();
    const confirm = this.confirmPassword().trim();

    if (pw && pw.length < 8) {
      this.errorMessage.set(this.translate.instant('ERROR.PASSWORD_MIN_LENGTH'));
      return;
    }
    if (pw && pw !== confirm) {
      this.errorMessage.set(this.translate.instant('ERROR.PASSWORDS_NO_MATCH'));
      return;
    }
    if (pw && !this.currentPassword()) {
      this.errorMessage.set(this.translate.instant('ERROR.CURRENT_PASSWORD_REQUIRED'));
      return;
    }

    const payload: Record<string, string> = {
      first_name: this.firstName().trim(),
      last_name: this.lastName().trim(),
    };
    if (this.isAdmin()) {
      payload['email'] = this.email().trim();
    }

    if (pw) {
      payload['password'] = pw;
      payload['current_password'] = this.currentPassword();
    }

    this.saving.set(true);
    this.usersApi.patch(this.userId, payload).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.currentPassword.set('');
        this.newPassword.set('');
        this.confirmPassword.set('');
        this.saving.set(false);
        this.toast.show(this.translate.instant('TOAST.PROFILE_UPDATED'));
      },
      error: (err) => {
        this.errorMessage.set(err?.error?.detail ?? this.translate.instant('ERROR.SOMETHING_WRONG'));
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
    });
  }

  onAvatarSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.authApi.uploadAvatar(file).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: res => {
        this.avatarUrl.set(res.avatar_url);
        this.auth.init();
        this.toast.show(this.translate.instant('TOAST.AVATAR_UPDATED'));
      },
      error: (err) => this.toast.show(err?.error?.detail ?? this.translate.instant('TOAST.FAILED_UPLOAD_AVATAR'), 'error'),
    });
  }

  removeAvatar(): void {
    this.authApi.deleteAvatar().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.avatarUrl.set(null);
        this.auth.init();
        this.toast.show(this.translate.instant('TOAST.AVATAR_REMOVED'));
      },
    });
  }
}
