import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { Task, TaskDependency, TasksApiService } from '../../../../core/tasks/tasks-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-dependencies',
  standalone: true,
  imports: [FormsModule, TranslateModule, ConfirmDialogComponent],
  templateUrl: './task-dependencies.component.html',
  styleUrl: './task-dependencies.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskDependenciesComponent implements OnInit {
  private readonly tasksApi = inject(TasksApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();
  boardTasks = input.required<Task[]>();

  dependencies = signal<TaskDependency[]>([]);
  selectedTaskId = signal<number | null>(null);
  pendingRemoveDep = signal<TaskDependency | null>(null);

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
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_ADD_DEPENDENCY'), 'error'),
      });
  }

  removeDependency(dep: TaskDependency): void {
    this.pendingRemoveDep.set(dep);
  }

  confirmRemoveDependency(): void {
    const dep = this.pendingRemoveDep();
    if (!dep) return;
    this.pendingRemoveDep.set(null);
    this.tasksApi.removeDependency(this.taskId(), dep.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.dependencies.update(list => list.filter(d => d.id !== dep.id));
          this.updateAvailable();
        },
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_REMOVE_DEPENDENCY'), 'error'),
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
