import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { HistoryEntry, TasksApiService } from '../../../../core/tasks/tasks-api.service';

@Component({
  selector: 'app-task-history',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './task-history.component.html',
  styleUrl: './task-history.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskHistoryComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();

  entries = signal<HistoryEntry[]>([]);
  expanded = signal(false);

  ngOnInit(): void {
    this.tasksApi.getHistory(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(entries => this.entries.set(entries));
  }
}
