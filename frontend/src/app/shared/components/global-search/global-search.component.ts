import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, inject, signal, HostListener } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';
import { Task, TasksApiService } from '../../../core/tasks/tasks-api.service';
import { TranslateModule } from '@ngx-translate/core';

type SearchResult = Task & { board_title: string };

@Component({
  selector: 'app-global-search',
  standalone: true,
  imports: [FormsModule, TranslateModule],
  templateUrl: './global-search.component.html',
  styleUrl: './global-search.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GlobalSearchComponent {
  private readonly tasksApi = inject(TasksApiService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly elementRef = inject(ElementRef);

  query = signal('');
  results = signal<SearchResult[]>([]);
  open = signal(false);
  loading = signal(false);

  private readonly search$ = new Subject<string>();

  constructor() {
    this.search$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => {
        if (q.length < 2) {
          this.results.set([]);
          this.loading.set(false);
          return of([]);
        }
        this.loading.set(true);
        return this.tasksApi.searchTasks(q);
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(results => {
      this.results.set(results);
      this.loading.set(false);
    });
  }

  onInput(value: string): void {
    this.query.set(value);
    this.open.set(true);
    this.search$.next(value);
  }

  openResult(result: SearchResult): void {
    this.open.set(false);
    this.query.set('');
    this.results.set([]);
    this.router.navigate(['/boards', result.board]);
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.open.set(false);
    }
  }
}
