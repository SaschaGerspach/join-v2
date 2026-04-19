import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import { UsersApiService } from '../../../../core/users/users-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [FormsModule, ConfirmDialogComponent, LoadingSpinnerComponent],
  templateUrl: './profile-page.component.html',
  styleUrl: './profile-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfilePageComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly usersApi = inject(UsersApiService);
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

  initials = computed(() => {
    const f = this.firstName()[0] ?? '';
    const l = this.lastName()[0] ?? '';
    return (f + l).toUpperCase() || (this.email()[0]?.toUpperCase() ?? '?');
  });

  private userId = 0;

  ngOnInit(): void {
    const user = this.auth.user();
    if (!user) return;
    this.userId = Number(user.id);

    this.usersApi.get(this.userId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (profile) => {
        this.firstName.set(profile.first_name);
        this.lastName.set(profile.last_name);
        this.email.set(profile.email);
        this.loading.set(false);
      },
      error: () => { this.toast.show('Failed to load profile.', 'error'); this.loading.set(false); },
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
}
