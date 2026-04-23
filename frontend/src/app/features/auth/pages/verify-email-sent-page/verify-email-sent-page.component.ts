import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { PendingEmailService } from '../../../../core/auth/pending-email.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { LanguageService } from '../../../../shared/services/language.service';

@Component({
  selector: 'app-verify-email-sent-page',
  standalone: true,
  imports: [RouterModule, FormsModule, TranslateModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <select class="auth-lang-select" [ngModel]="lang.currentLang()" (ngModelChange)="lang.setLanguage($event)">
          <option value="en">EN</option>
          <option value="de">DE</option>
        </select>
        <h1>{{ 'AUTH.CHECK_INBOX' | translate }}</h1>
        <div class="auth-divider"></div>
        <p class="info-message" [innerHTML]="'AUTH.VERIFICATION_SENT' | translate:{ email: email() }"></p>
        @if (sent()) {
          <p class="info-message success">{{ 'AUTH.VERIFICATION_RESENT' | translate }}</p>
        }
        @if (error()) {
          <p class="error-message">{{ error() }}</p>
        }
        <div class="auth-actions">
          <button class="btn-secondary" (click)="resend()" [disabled]="resending()">
            {{ resending() ? ('AUTH.SENDING' | translate) : ('AUTH.RESEND_EMAIL' | translate) }}
          </button>
          <a routerLink="/login" class="btn-primary">{{ 'AUTH.GO_TO_LOGIN' | translate }}</a>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VerifyEmailSentPageComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly pendingEmail = inject(PendingEmailService);
  private readonly router = inject(Router);
  private readonly translate = inject(TranslateService);
  readonly lang = inject(LanguageService);

  email = signal('');
  resending = signal(false);
  sent = signal(false);
  error = signal('');

  ngOnInit(): void {
    const email = this.pendingEmail.consume();
    if (!email) {
      this.router.navigate(['/register']);
      return;
    }
    this.email.set(email);
  }

  resend(): void {
    if (!this.email()) return;
    this.resending.set(true);
    this.sent.set(false);
    this.authApi.resendVerification(this.email()).subscribe({
      next: () => { this.sent.set(true); this.resending.set(false); },
      error: () => { this.error.set(this.translate.instant('AUTH.RESEND_FAILED')); this.resending.set(false); },
    });
  }
}
