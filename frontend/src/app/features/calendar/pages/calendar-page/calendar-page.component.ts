import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { TaskDetailModalComponent } from '../../../boards/components/task-detail-modal/task-detail-modal.component';

@Component({
  selector: 'app-calendar-page',
  standalone: true,
  imports: [TaskDetailModalComponent],
  templateUrl: './calendar-page.component.html',
  styleUrl: './calendar-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CalendarPageComponent implements OnInit {
  private readonly boardsApi = inject(BoardsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly destroyRef = inject(DestroyRef);

  viewDate = signal(new Date());
  tasks = signal<Task[]>([]);
  columnsByBoard = signal<Record<number, Column[]>>({});
  selectedTask = signal<Task | null>(null);
  loading = signal(true);

  readonly weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  monthLabel = computed(() => {
    return this.viewDate().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  });

  calendarDays = computed(() => {
    const d = this.viewDate();
    const year = d.getFullYear();
    const month = d.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // Start on Monday (0=Sun → 6, 1=Mon → 0, ...)
    let startOffset = firstDay.getDay() - 1;
    if (startOffset < 0) startOffset = 6;

    const days: (Date | null)[] = [];
    for (let i = 0; i < startOffset; i++) days.push(null);
    for (let i = 1; i <= lastDay.getDate(); i++) days.push(new Date(year, month, i));

    // Pad to full weeks
    while (days.length % 7 !== 0) days.push(null);
    return days;
  });

  ngOnInit(): void {
    this.boardsApi.getAll().pipe(
      takeUntilDestroyed(this.destroyRef),
      switchMap(boards => {
        const taskRequests = boards.map(b => this.tasksApi.getByBoard(b.id));
        const colRequests = boards.map(b => this.columnsApi.getByBoard(b.id).pipe());
        return forkJoin({
          allTasks: forkJoin(taskRequests.length ? taskRequests : [Promise.resolve([])]),
          allCols: forkJoin(colRequests.length ? colRequests : [Promise.resolve([])]),
          boards: Promise.resolve(boards),
        });
      })
    ).subscribe({
      next: ({ allTasks, allCols, boards }) => {
        this.tasks.set((allTasks as Task[][]).flat().filter(t => !!t.due_date));

        const cbMap: Record<number, Column[]> = {};
        boards.forEach((b, i) => { cbMap[b.id] = (allCols as Column[][])[i] ?? []; });
        this.columnsByBoard.set(cbMap);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  tasksByDate = computed(() => {
    const map: Record<string, Task[]> = {};
    for (const t of this.tasks()) {
      const key = t.due_date?.slice(0, 10);
      if (key) (map[key] ??= []).push(t);
    }
    return map;
  });

  tasksForDay(day: Date): Task[] {
    return this.tasksByDate()[day.toISOString().slice(0, 10)] ?? [];
  }

  columnsForTask(task: Task): Column[] {
    return this.columnsByBoard()[task.board] ?? [];
  }

  isToday(day: Date): boolean {
    return day.toISOString().slice(0, 10) === new Date().toISOString().slice(0, 10);
  }

  prevMonth(): void {
    const d = this.viewDate();
    this.viewDate.set(new Date(d.getFullYear(), d.getMonth() - 1, 1));
  }

  nextMonth(): void {
    const d = this.viewDate();
    this.viewDate.set(new Date(d.getFullYear(), d.getMonth() + 1, 1));
  }

  openTask(task: Task): void {
    this.selectedTask.set(task);
  }

  onTaskUpdated(updated: Task): void {
    this.tasks.update(list => list.map(t => t.id === updated.id ? updated : t));
  }

  onTaskDeleted(id: number): void {
    this.tasks.update(list => list.filter(t => t.id !== id));
    this.selectedTask.set(null);
  }

  priorityClass(priority: string): string {
    return `priority-${priority}`;
  }
}
