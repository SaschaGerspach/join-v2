import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { AuthService } from '../../../../core/auth/auth.service';
import { AuthApiService, TotpSetupResponse } from '../../../../core/auth/auth-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-profile-two-factor',
  imports: [FormsModule, TranslateModule],
  templateUrl: './profile-two-factor.component.html',
  styleUrl: './profile-two-factor.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfileTwoFactorComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  totpEnabled = signal(inject(AuthService).user()?.totp_enabled ?? false);
  totpSetup = signal<TotpSetupResponse | null>(null);
  totpConfirmCode = signal('');
  totpDisableCode = signal('');
  totpDisablePassword = signal('');
  totpError = signal('');

  startTotpSetup(): void {
    this.totpError.set('');
    this.authApi.totpSetup().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (res) => this.totpSetup.set(res),
    });
  }

  confirmTotp(): void {
    const code = this.totpConfirmCode().trim();
    if (code.length !== 6) { this.totpError.set(this.translate.instant('ERROR.ENTER_6_DIGIT')); return; }
    this.totpError.set('');
    this.authApi.totpConfirm(code).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.totpEnabled.set(true);
        this.totpSetup.set(null);
        this.totpConfirmCode.set('');
        this.toast.show(this.translate.instant('TOAST.TOTP_ENABLED'));
      },
      error: () => this.totpError.set(this.translate.instant('TOAST.INVALID_TOTP_CODE')),
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
    if (!password) { this.totpError.set(this.translate.instant('ERROR.PASSWORD_REQUIRED')); return; }
    if (code.length !== 6) { this.totpError.set(this.translate.instant('ERROR.ENTER_6_DIGIT')); return; }
    this.totpError.set('');
    this.authApi.totpDisable(password, code).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.totpEnabled.set(false);
        this.totpDisableCode.set('');
        this.totpDisablePassword.set('');
        this.toast.show(this.translate.instant('TOAST.TOTP_DISABLED'));
      },
      error: (err) => this.totpError.set(err?.error?.detail ?? this.translate.instant('TOAST.FAILED_DISABLE_TOTP')),
    });
  }
}
