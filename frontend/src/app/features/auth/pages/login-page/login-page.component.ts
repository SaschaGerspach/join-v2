import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { FormsModule, NgForm } from '@angular/forms';
import { AuthService } from '../../../../core/auth/auth.service';
import { PendingEmailService } from '../../../../core/auth/pending-email.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [FormsModule, RouterModule],
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPageComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly pendingEmail = inject(PendingEmailService);

  email = '';
  password = '';
  error = signal<string | null>(null);
  showPassword = signal(false);
  submitting = signal(false);

  unverifiedEmail = signal<string | null>(null);

  resendVerification(): void {
    const email = this.unverifiedEmail();
    if (email) {
      this.pendingEmail.set(email);
      this.router.navigate(['/verify-email-sent']);
    }
  }

  login(form: NgForm): void {
    if (form.invalid) return;
    this.error.set(null);
    this.unverifiedEmail.set(null);
    this.submitting.set(true);
    this.auth.login(this.email, this.password).subscribe({
      next: () => this.router.navigate(['/boards']),
      error: (err) => {
        if (err?.error?.code === 'email_not_verified') {
          this.unverifiedEmail.set(this.email);
        } else {
          this.error.set('Invalid email or password.');
        }
        this.submitting.set(false);
      },
    });
  }
}
