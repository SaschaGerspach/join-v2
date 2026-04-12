import { Component, inject, signal, OnInit } from '@angular/core';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { AuthApiService } from '../../../../core/auth/auth-api.service';

@Component({
  selector: 'app-verify-email-page',
  standalone: true,
  imports: [RouterModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        @if (loading()) {
          <p class="info-message">Verifying…</p>
        } @else if (success()) {
          <h1>Email verified!</h1>
          <div class="auth-divider"></div>
          <p class="info-message">Your account is now active. You can log in.</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-primary">Go to login</a>
          </div>
        } @else {
          <h1>Verification failed</h1>
          <div class="auth-divider"></div>
          <p class="error-message">{{ error() }}</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-secondary">Back to login</a>
          </div>
        }
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
})
export class VerifyEmailPageComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);

  loading = signal(true);
  success = signal(false);
  error = signal('');

  ngOnInit(): void {
    const uid = this.route.snapshot.paramMap.get('uid') ?? '';
    const token = this.route.snapshot.paramMap.get('token') ?? '';
    this.authApi.verifyEmail(uid, token).subscribe({
      next: () => { this.success.set(true); this.loading.set(false); },
      error: (err) => { this.error.set(err?.error?.detail ?? 'Invalid or expired link.'); this.loading.set(false); },
    });
  }
}
