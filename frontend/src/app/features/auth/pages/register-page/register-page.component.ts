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

  register(form: NgForm): void {
    if (form.invalid) return;
    this.error.set(null);
    this.api.register({
      email: this.email,
      password: this.password,
      first_name: this.firstName,
      last_name: this.lastName,
    }).subscribe({
      next: (user) => {
        this.auth.login(this.email, this.password).subscribe({
          next: () => this.router.navigate(['/boards']),
          error: () => this.router.navigate(['/login']),
        });
      },
      error: (err) => this.error.set(err?.error?.detail ?? 'Registration failed. Email may already be in use.'),
    });
  }
}
