import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { SlicePipe } from '@angular/common';
import { LoadingSpinnerComponent } from '../../../../shared/components/loading-spinner/loading-spinner.component';
import { AuthService } from '../../../../core/auth/auth.service';
import { BoardsApiService, Board } from '../../../../core/boards/boards-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { forkJoin, of, switchMap } from 'rxjs';

@Component({
  selector: 'app-summary-page',
  standalone: true,
  imports: [SlicePipe, LoadingSpinnerComponent],
  templateUrl: './summary-page.component.html',
  styleUrl: './summary-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SummaryPageComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  loading = signal(true);
  boards = signal<Board[]>([]);
  tasks = signal<Task[]>([]);

  userName = computed(() => {
    const user = this.auth.user();
    if (!user) return '';
    return user.first_name || user.email.split('@')[0];
  });

  totalTasks = computed(() => this.tasks().length);
  urgentTasks = computed(() => this.tasks().filter(t => t.priority === 'urgent').length);
  highTasks = computed(() => this.tasks().filter(t => t.priority === 'high').length);

  overdueTasks = computed(() => {
    const today = new Date(new Date().toDateString());
    return this.tasks().filter(t => t.due_date && new Date(t.due_date) < today).length;
  });

  nextDeadline = computed(() => {
    const upcoming = this.tasks()
      .filter(t => t.due_date)
      .sort((a, b) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime());
    return upcoming[0]?.due_date ?? null;
  });

  greeting = computed(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  });

  ngOnInit(): void {
    this.boardsApi.getAll().pipe(
      switchMap(boards => {
        this.boards.set(boards);
        if (boards.length === 0) {
          return of([] as Task[][]);
        }
        return forkJoin(boards.map(b => this.tasksApi.getByBoard(b.id)));
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: taskArrays => { this.tasks.set(taskArrays.flat()); this.loading.set(false); },
      error: () => { this.tasks.set([]); this.loading.set(false); },
    });
  }

  goToBoards(): void {
    this.router.navigate(['/boards']);
  }
}
