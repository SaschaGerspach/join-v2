import { Component, inject, signal, OnInit } from '@angular/core';
import { RouterModule, Router } from '@angular/router';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { PendingEmailService } from '../../../../core/auth/pending-email.service';

@Component({
  selector: 'app-verify-email-sent-page',
  standalone: true,
  imports: [RouterModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <h1>Check your inbox</h1>
        <div class="auth-divider"></div>
        <p class="info-message">
          We sent a verification link to <strong>{{ email() }}</strong>.
          Click it to activate your account.
        </p>
        @if (sent()) {
          <p class="info-message success">Verification email resent.</p>
        }
        @if (error()) {
          <p class="error-message">{{ error() }}</p>
        }
        <div class="auth-actions">
          <button class="btn-secondary" (click)="resend()" [disabled]="resending()">
            {{ resending() ? 'Sending…' : 'Resend email' }}
          </button>
          <a routerLink="/login" class="btn-primary">Go to login</a>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
})
export class VerifyEmailSentPageComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly pendingEmail = inject(PendingEmailService);
  private readonly router = inject(Router);

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
      error: () => { this.error.set('Failed to resend. Try again.'); this.resending.set(false); },
    });
  }
}
