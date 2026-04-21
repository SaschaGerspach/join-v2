import { ChangeDetectionStrategy, Component, ElementRef, inject, signal, computed, HostListener, OnInit, OnDestroy } from '@angular/core';
import { Router, RouterModule } from "@angular/router";
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/auth/auth.service';
import { ToastComponent } from '../../shared/components/toast/toast.component';
import { ThemeService } from '../../shared/services/theme.service';
import { LanguageService } from '../../shared/services/language.service';
import { NotificationService } from '../../core/notifications/notification.service';
import { KeyboardShortcutsModalComponent } from '../../shared/components/keyboard-shortcuts-modal/keyboard-shortcuts-modal.component';
import { GlobalSearchComponent } from '../../shared/components/global-search/global-search.component';
import { OfflineBannerComponent } from '../../shared/components/offline-banner/offline-banner.component';
import { UserAvatarComponent } from '../../shared/components/user-avatar/user-avatar.component';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterModule, DatePipe, FormsModule, ToastComponent, KeyboardShortcutsModalComponent, GlobalSearchComponent, OfflineBannerComponent, UserAvatarComponent, TranslateModule],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShellComponent implements OnInit, OnDestroy {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  readonly lang = inject(LanguageService);
  readonly notificationService = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly elementRef = inject(ElementRef);

  menuOpen = signal(false);
  showShortcuts = signal(false);
  notificationsOpen = signal(false);
  sidebarOpen = signal(false);

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    if (!this.elementRef.nativeElement.querySelector('.header-right')?.contains(event.target)) {
      this.menuOpen.set(false);
      this.notificationsOpen.set(false);
    }
  }

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

  ngOnInit(): void {
    this.lang.init();
    this.notificationService.connect();
  }

  ngOnDestroy(): void {
    this.notificationService.disconnect();
  }

  toggleMenu(): void {
    this.menuOpen.update(v => !v);
  }

  toggleSidebar(): void {
    this.sidebarOpen.update(v => !v);
  }

  closeSidebar(): void {
    this.sidebarOpen.set(false);
  }

  toggleNotifications(): void {
    this.notificationsOpen.update(v => !v);
    this.menuOpen.set(false);
  }

  openNotification(notification: { board_id: number | null; id: number }): void {
    this.notificationService.markAsRead(notification.id);
    this.notificationsOpen.set(false);
    if (notification.board_id) {
      this.router.navigate(['/boards', notification.board_id]);
    }
  }

  logout(): void {
    this.notificationService.disconnect();
    this.auth.logout();
    this.menuOpen.set(false);
    this.router.navigate(['/login']);
  }
}
