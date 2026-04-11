import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login-page.component.html',
})
export class LoginPageComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  email = '';
  password = '';
  error = signal<string | null>(null);

  login(): void {
    this.error.set(null);
    this.auth.login(this.email, this.password).subscribe({
      next: () => this.router.navigate(['/boards']),
      error: () => this.error.set('Invalid email or password.'),
    });
  }
}
