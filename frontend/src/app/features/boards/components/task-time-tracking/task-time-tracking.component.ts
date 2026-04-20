import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { TimeEntry, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-time-tracking',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './task-time-tracking.component.html',
  styleUrl: './task-time-tracking.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskTimeTrackingComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();

  entries = signal<TimeEntry[]>([]);
  totalMinutes = signal(0);
  newDuration = signal('');
  newNote = signal('');

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.tasksApi.getTimeEntries(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(data => {
        this.entries.set(data.entries);
        this.totalMinutes.set(data.total_minutes);
      });
  }

  logTime(): void {
    const minutes = parseInt(this.newDuration(), 10);
    if (!minutes || minutes < 1) return;
    this.tasksApi.logTime(this.taskId(), minutes, this.newNote())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: entry => {
          this.entries.update(list => [entry, ...list]);
          this.totalMinutes.update(t => t + entry.duration_minutes);
          this.newDuration.set('');
          this.newNote.set('');
        },
        error: () => this.toast.show('Failed to log time.', 'error'),
      });
  }

  deleteEntry(entry: TimeEntry): void {
    this.tasksApi.deleteTimeEntry(this.taskId(), entry.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.entries.update(list => list.filter(e => e.id !== entry.id));
          this.totalMinutes.update(t => t - entry.duration_minutes);
        },
        error: () => this.toast.show('Failed to delete entry.', 'error'),
      });
  }

  formatDuration(minutes: number): string {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }
}
