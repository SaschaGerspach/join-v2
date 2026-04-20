import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Task, TaskDependency, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-dependencies',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './task-dependencies.component.html',
  styleUrl: './task-dependencies.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskDependenciesComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();
  boardTasks = input.required<Task[]>();

  dependencies = signal<TaskDependency[]>([]);
  selectedTaskId = signal<number | null>(null);

  availableTasks = signal<Task[]>([]);

  ngOnInit(): void {
    this.tasksApi.getDependencies(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(deps => {
        this.dependencies.set(deps);
        this.updateAvailable();
      });
  }

  addDependency(): void {
    const id = this.selectedTaskId();
    if (!id) return;
    this.tasksApi.addDependency(this.taskId(), id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: dep => {
          this.dependencies.update(list => [...list, dep]);
          this.selectedTaskId.set(null);
          this.updateAvailable();
        },
        error: () => this.toast.show('Failed to add dependency.', 'error'),
      });
  }

  removeDependency(dep: TaskDependency): void {
    this.tasksApi.removeDependency(this.taskId(), dep.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.dependencies.update(list => list.filter(d => d.id !== dep.id));
          this.updateAvailable();
        },
        error: () => this.toast.show('Failed to remove dependency.', 'error'),
      });
  }

  private updateAvailable(): void {
    const depIds = new Set(this.dependencies().map(d => d.depends_on));
    const currentId = this.taskId();
    this.availableTasks.set(
      this.boardTasks().filter(t => t.id !== currentId && !depIds.has(t.id))
    );
  }
}
