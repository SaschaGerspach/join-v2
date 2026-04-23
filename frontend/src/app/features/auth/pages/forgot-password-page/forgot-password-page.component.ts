import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { LanguageService } from '../../../../shared/services/language.service';

@Component({
  selector: 'app-forgot-password-page',
  standalone: true,
  imports: [FormsModule, RouterModule, TranslateModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <select class="auth-lang-select" [ngModel]="lang.currentLang()" (ngModelChange)="lang.setLanguage($event)">
          <option value="en">EN</option>
          <option value="de">DE</option>
        </select>
        <h1>{{ 'AUTH.RESET_PASSWORD' | translate }}</h1>
        <div class="auth-divider"></div>

        @if (sent()) {
          <p class="info-message">{{ 'AUTH.RESET_SENT' | translate }}</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-secondary">{{ 'AUTH.BACK_TO_LOGIN' | translate }}</a>
          </div>
        } @else {
          <form #f="ngForm" (ngSubmit)="submit(f)">
            <div class="form-group">
              <input
                class="form-input"
                type="email"
                [(ngModel)]="email"
                name="email"
                [placeholder]="'AUTH.EMAIL' | translate"
                required
                email
                #emailField="ngModel"
                [class.input-error]="emailField.invalid && (emailField.touched || f.submitted)"
              />
              @if (emailField.invalid && (emailField.touched || f.submitted)) {
                <span class="field-error">{{ 'AUTH.EMAIL_INVALID' | translate }}</span>
              }
            </div>
            @if (error()) {
              <p class="error-message">{{ error() }}</p>
            }
            <div class="auth-actions">
              <button type="submit" class="btn-primary" [disabled]="submitting()">
                {{ submitting() ? ('AUTH.SENDING' | translate) : ('AUTH.SEND_RESET_LINK' | translate) }}
              </button>
              <a routerLink="/login" class="btn-secondary">{{ 'COMMON.CANCEL' | translate }}</a>
            </div>
          </form>
        }
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ForgotPasswordPageComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly translate = inject(TranslateService);
  readonly lang = inject(LanguageService);

  email = '';
  submitting = signal(false);
  sent = signal(false);
  error = signal<string | null>(null);

  submit(form: NgForm): void {
    if (form.invalid) return;
    this.error.set(null);
    this.submitting.set(true);
    this.authApi.passwordResetRequest(this.email).subscribe({
      next: () => { this.sent.set(true); this.submitting.set(false); },
      error: () => { this.error.set(this.translate.instant('AUTH.SOMETHING_WRONG')); this.submitting.set(false); },
    });
  }
}
