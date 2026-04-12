import { TestBed } from '@angular/core/testing';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;

  beforeEach(() => {
    localStorage.clear();
    service = TestBed.inject(ThemeService);
  });

  it('should toggle from light to dark', () => {
    service['apply'](false);
    service.toggle();
    expect(service.isDark()).toBeTrue();
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('should toggle from dark to light', () => {
    service['apply'](true);
    service.toggle();
    expect(service.isDark()).toBeFalse();
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('should read stored preference', () => {
    localStorage.setItem('theme', 'dark');
    const s = new ThemeService();
    expect(s.isDark()).toBeTrue();
  });
});
