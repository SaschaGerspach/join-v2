import { ChangeDetectionStrategy, Component, signal, OnInit, OnDestroy } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';

const DISMISS_KEY = 'install_prompt_dismissed';
const DISMISS_DAYS = 7;

@Component({
  selector: 'app-install-prompt',
  standalone: true,
  imports: [TranslateModule],
  template: `
    @if (showPrompt()) {
      <div class="install-banner" role="complementary">
        <span>{{ 'INSTALL.PROMPT' | translate }}</span>
        <button class="install-btn" (click)="install()">{{ 'INSTALL.INSTALL' | translate }}</button>
        <button class="dismiss-btn" (click)="dismiss()">{{ 'INSTALL.DISMISS' | translate }}</button>
      </div>
    }
  `,
  styles: [`
    .install-banner {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 10px 16px;
      background: #2e7d32;
      color: #fff;
      text-align: center;
      font-size: 0.85rem;
      font-weight: 500;
      z-index: 9997;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
    }
    .install-btn {
      background: #fff;
      color: #2e7d32;
      border: none;
      border-radius: 6px;
      padding: 4px 14px;
      font-weight: 700;
      font-size: 0.82rem;
      cursor: pointer;
    }
    .install-btn:hover { opacity: 0.9; }
    .dismiss-btn {
      background: none;
      border: 1px solid rgba(255,255,255,0.5);
      border-radius: 6px;
      padding: 4px 10px;
      color: #fff;
      font-size: 0.8rem;
      cursor: pointer;
    }
    .dismiss-btn:hover { border-color: #fff; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InstallPromptComponent implements OnInit, OnDestroy {
  showPrompt = signal(false);
  private deferredPrompt: BeforeInstallPromptEvent | null = null;
  private readonly onBeforeInstall = (e: Event) => this.handlePrompt(e as BeforeInstallPromptEvent);

  ngOnInit(): void {
    if (this.isDismissed()) return;
    window.addEventListener('beforeinstallprompt', this.onBeforeInstall);
  }

  ngOnDestroy(): void {
    window.removeEventListener('beforeinstallprompt', this.onBeforeInstall);
  }

  private handlePrompt(e: BeforeInstallPromptEvent): void {
    e.preventDefault();
    this.deferredPrompt = e;
    this.showPrompt.set(true);
  }

  install(): void {
    if (!this.deferredPrompt) return;
    this.deferredPrompt.prompt();
    this.deferredPrompt.userChoice.then(() => {
      this.deferredPrompt = null;
      this.showPrompt.set(false);
    });
  }

  dismiss(): void {
    localStorage.setItem(DISMISS_KEY, String(Date.now()));
    this.showPrompt.set(false);
  }

  private isDismissed(): boolean {
    const ts = localStorage.getItem(DISMISS_KEY);
    if (!ts) return false;
    return Date.now() - Number(ts) < DISMISS_DAYS * 24 * 60 * 60 * 1000;
  }
}

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}
