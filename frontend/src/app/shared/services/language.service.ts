import { Injectable, inject, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

const STORAGE_KEY = 'join_language';
const SUPPORTED_LANGS = ['en', 'de'] as const;
type Lang = typeof SUPPORTED_LANGS[number];

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private readonly translate = inject(TranslateService);
  readonly currentLang = signal<Lang>(this.getInitialLang());

  init(): void {
    this.translate.setDefaultLang('en');
    this.translate.use(this.currentLang());
  }

  setLanguage(lang: Lang): void {
    this.currentLang.set(lang);
    this.translate.use(lang);
    localStorage.setItem(STORAGE_KEY, lang);
    document.documentElement.lang = lang;
  }

  private getInitialLang(): Lang {
    const stored = localStorage.getItem(STORAGE_KEY) as Lang | null;
    if (stored && SUPPORTED_LANGS.includes(stored)) return stored;
    const browserLang = navigator.language.split('-')[0] as Lang;
    return SUPPORTED_LANGS.includes(browserLang) ? browserLang : 'en';
  }
}
