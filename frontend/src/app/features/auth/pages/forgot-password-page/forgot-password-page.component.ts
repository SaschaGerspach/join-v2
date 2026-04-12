import { Component, inject, signal } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthApiService } from '../../../../core/auth/auth-api.service';

@Component({
  selector: 'app-forgot-password-page',
  standalone: true,
  imports: [FormsModule, RouterModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <h1>Reset password</h1>
        <div class="auth-divider"></div>

        @if (sent()) {
          <p class="info-message">If an account exists for this email, you will receive a reset link shortly.</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-secondary">Back to login</a>
          </div>
        } @else {
          <form #f="ngForm" (ngSubmit)="submit(f)">
            <div class="form-group">
              <input
                class="form-input"
                type="email"
                [(ngModel)]="email"
                name="email"
                placeholder="Email"
                required
                email
                #emailField="ngModel"
                [class.input-error]="emailField.invalid && (emailField.touched || f.submitted)"
              />
              @if (emailField.invalid && (emailField.touched || f.submitted)) {
                <span class="field-error">Enter a valid email address.</span>
              }
            </div>
            @if (error()) {
              <p class="error-message">{{ error() }}</p>
            }
            <div class="auth-actions">
              <button type="submit" class="btn-primary" [disabled]="submitting()">
                {{ submitting() ? 'Sending…' : 'Send reset link' }}
              </button>
              <a routerLink="/login" class="btn-secondary">Cancel</a>
            </div>
          </form>
        }
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
})
export class ForgotPasswordPageComponent {
  private readonly authApi = inject(AuthApiService);

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
      error: () => { this.error.set('Something went wrong. Please try again.'); this.submitting.set(false); },
    });
  }
}
