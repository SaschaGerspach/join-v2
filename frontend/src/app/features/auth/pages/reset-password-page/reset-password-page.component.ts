import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { AuthApiService } from '../../../../core/auth/auth-api.service';

@Component({
  selector: 'app-reset-password-page',
  standalone: true,
  imports: [FormsModule, RouterModule],
  template: `
    <div class="auth-page">
      <div class="auth-logo"><span>Join</span></div>
      <div class="auth-card">
        <h1>Set new password</h1>
        <div class="auth-divider"></div>

        @if (done()) {
          <p class="info-message">Password updated. You can now log in.</p>
          <div class="auth-actions">
            <a routerLink="/login" class="btn-primary">Go to login</a>
          </div>
        } @else {
          <form #f="ngForm" (ngSubmit)="submit(f)">
            <div class="form-group">
              <input
                class="form-input"
                type="password"
                [(ngModel)]="password"
                name="password"
                placeholder="New password"
                required
                minlength="8"
                #pwField="ngModel"
                [class.input-error]="pwField.invalid && (pwField.touched || f.submitted)"
              />
              @if (pwField.invalid && (pwField.touched || f.submitted)) {
                <span class="field-error">Password must be at least 8 characters.</span>
              }
            </div>
            <div class="form-group">
              <input
                class="form-input"
                type="password"
                [(ngModel)]="confirm"
                name="confirm"
                placeholder="Confirm password"
                required
                #confirmField="ngModel"
                [class.input-error]="confirmField.invalid && (confirmField.touched || f.submitted)"
              />
            </div>
            @if (error()) {
              <p class="error-message">{{ error() }}</p>
            }
            <div class="auth-actions">
              <button type="submit" class="btn-primary" [disabled]="submitting()">
                {{ submitting() ? 'Saving…' : 'Set password' }}
              </button>
            </div>
          </form>
        }
      </div>
    </div>
  `,
  styleUrls: ['../login-page/login-page.component.scss'],
})
export class ResetPasswordPageComponent implements OnInit {
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);

  password = '';
  confirm = '';
  submitting = signal(false);
  done = signal(false);
  error = signal<string | null>(null);

  private uid = '';
  private token = '';

  ngOnInit(): void {
    this.uid = this.route.snapshot.paramMap.get('uid') ?? '';
    this.token = this.route.snapshot.paramMap.get('token') ?? '';
  }

  submit(form: NgForm): void {
    if (form.invalid) return;
    if (this.password !== this.confirm) {
      this.error.set('Passwords do not match.');
      return;
    }
    this.error.set(null);
    this.submitting.set(true);
    this.authApi.passwordResetConfirm(this.uid, this.token, this.password).subscribe({
      next: () => { this.done.set(true); this.submitting.set(false); },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Invalid or expired link.');
        this.submitting.set(false);
      },
    });
  }
}
