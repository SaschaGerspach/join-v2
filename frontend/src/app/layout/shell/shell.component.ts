import { ChangeDetectionStrategy, Component, inject, signal, computed, HostListener } from '@angular/core';
import { Router, RouterModule } from "@angular/router";
import { AuthService } from '../../core/auth/auth.service';
import { ToastComponent } from '../../shared/components/toast/toast.component';
import { ThemeService } from '../../shared/services/theme.service';
import { KeyboardShortcutsModalComponent } from '../../shared/components/keyboard-shortcuts-modal/keyboard-shortcuts-modal.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterModule, ToastComponent, KeyboardShortcutsModalComponent],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShellComponent {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  private readonly router = inject(Router);

  menuOpen = signal(false);
  showShortcuts = signal(false);

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement) return;
    if (event.key === '?') {
      event.preventDefault();
      this.showShortcuts.update(v => !v);
    }
  }

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
