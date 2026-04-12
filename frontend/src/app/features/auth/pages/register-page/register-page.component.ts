import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule, NgForm } from '@angular/forms';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './register-page.component.html',
  styleUrl: './register-page.component.scss',
})
export class RegisterPageComponent {
  private readonly api = inject(AuthApiService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  firstName = '';
  lastName = '';
  email = '';
  password = '';
  error = signal<string | null>(null);
  showPassword = signal(false);
  submitting = signal(false);

  passwordStrength = signal<'weak' | 'medium' | 'strong' | null>(null);

  onPasswordChange(value: string): void {
    this.password = value;
    if (!value) { this.passwordStrength.set(null); return; }
    const hasUpper = /[A-Z]/.test(value);
    const hasDigit = /\d/.test(value);
    const hasSpecial = /[^A-Za-z0-9]/.test(value);
    const score = (value.length >= 12 ? 1 : 0) + (hasUpper ? 1 : 0) + (hasDigit ? 1 : 0) + (hasSpecial ? 1 : 0);
    this.passwordStrength.set(score >= 3 ? 'strong' : score >= 2 ? 'medium' : 'weak');
  }

  register(form: NgForm): void {
    if (form.invalid) return;
    this.error.set(null);
    this.submitting.set(true);
    this.api.register({
      email: this.email,
      password: this.password,
      first_name: this.firstName,
      last_name: this.lastName,
    }).subscribe({
      next: () => {
        this.auth.login(this.email, this.password).subscribe({
          next: () => this.router.navigate(['/boards']),
          error: () => this.router.navigate(['/login']),
        });
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Registration failed. Email may already be in use.');
        this.submitting.set(false);
      },
    });
  }
}
