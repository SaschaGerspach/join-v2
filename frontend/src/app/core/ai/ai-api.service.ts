import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';

export const AI_FEATURE = {
  generateDescription: 'generate_description',
  suggestSubtasks: 'suggest_subtasks',
  summarize: 'summarize',
  categorize: 'categorize',
} as const;

export type AiCategorization = { priority: string; labels: string[] };

@Injectable({ providedIn: 'root' })
export class AiApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  readonly enabled = signal<string[] | null>(null);
  private loading = false;

  /** Loads the set of enabled features once; safe to call from many components. */
  ensureLoaded(): void {
    if (this.enabled() !== null || this.loading) return;
    this.loading = true;
    this.http.get<{ features: string[] }>(`${this.baseUrl}/ai/features/`, { withCredentials: true })
      .subscribe({
        next: r => { this.enabled.set(r.features); this.loading = false; },
        error: () => { this.enabled.set([]); this.loading = false; },
      });
  }

  isEnabled(key: string): boolean {
    return this.enabled()?.includes(key) ?? false;
  }

  generateDescription(title: string, keywords?: string): Observable<string> {
    return this.http
      .post<{ description: string }>(`${this.baseUrl}/ai/generate-description/`, { title, keywords }, { withCredentials: true })
      .pipe(map(r => r.description));
  }

  suggestSubtasks(title: string, description?: string): Observable<string[]> {
    return this.http
      .post<{ subtasks: string[] }>(`${this.baseUrl}/ai/suggest-subtasks/`, { title, description }, { withCredentials: true })
      .pipe(map(r => r.subtasks));
  }

  categorize(title: string, description?: string): Observable<AiCategorization> {
    return this.http.post<AiCategorization>(`${this.baseUrl}/ai/categorize/`, { title, description }, { withCredentials: true });
  }
}
