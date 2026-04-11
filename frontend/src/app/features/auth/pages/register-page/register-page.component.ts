import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthApiService } from '../../../../core/auth/auth-api.service';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './register-page.component.html',
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

  register(): void {
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
      error: () => this.error.set('Registration failed. Email may already be in use.'),
    });
  }
}
