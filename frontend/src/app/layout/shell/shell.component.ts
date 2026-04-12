import { Component, inject, signal, computed } from '@angular/core';
import { Router, RouterModule } from "@angular/router";
import { AuthService } from '../../core/auth/auth.service';
import { ToastComponent } from '../../shared/components/toast/toast.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterModule, ToastComponent],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss'
})
export class ShellComponent {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  menuOpen = signal(false);

  userInitials = computed(() => {
    const user = this.auth.user();
    if (!user) return '';
    const parts = user.email.split('@')[0].split('.');
    return parts.map(p => p[0]?.toUpperCase() ?? '').join('').slice(0, 2);
  });

  toggleMenu(): void {
    this.menuOpen.update(v => !v);
  }

  logout(): void {
    this.auth.logout();
    this.menuOpen.set(false);
    this.router.navigate(['/login']);
  }
}
