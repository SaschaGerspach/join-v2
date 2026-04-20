import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly doc = inject(DOCUMENT);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  isDark = signal(false);

  constructor() {
    if (!this.isBrowser) return;
    const stored = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const dark = stored ? stored === 'dark' : prefersDark;
    this.apply(dark);
  }

  toggle(): void {
    this.apply(!this.isDark());
  }

  private apply(dark: boolean): void {
    this.isDark.set(dark);
    this.doc.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    if (this.isBrowser) {
      localStorage.setItem('theme', dark ? 'dark' : 'light');
    }
  }
}
