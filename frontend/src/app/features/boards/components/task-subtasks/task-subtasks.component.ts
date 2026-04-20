import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, output, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Subtask, SubtasksApiService } from '../../../../core/tasks/subtasks-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-subtasks',
  standalone: true,
  imports: [FormsModule, ConfirmDialogComponent],
  templateUrl: './task-subtasks.component.html',
  styleUrl: './task-subtasks.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskSubtasksComponent implements OnInit {
  private readonly subtasksApi = inject(SubtasksApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  taskId = input.required<number>();

  subtaskCountChanged = output<{ total: number; done: number }>();

  subtasks = signal<Subtask[]>([]);
  newSubtaskTitle = signal('');
  editingSubtaskId = signal<number | null>(null);
  editingSubtaskTitle = '';
  pendingDeleteSubtask = signal<Subtask | null>(null);

  ngOnInit(): void {
    this.subtasksApi.getByTask(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(subs => this.subtasks.set(subs));
  }

  addSubtask(): void {
    const title = this.newSubtaskTitle().trim();
    if (!title) return;
    this.subtasksApi.create(this.taskId(), title)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: sub => {
          this.subtasks.update(s => [...s, sub]);
          this.newSubtaskTitle.set('');
          this.emitCounts();
        },
        error: () => this.toast.show('Failed to add subtask.', 'error'),
      });
  }

  toggleSubtask(sub: Subtask): void {
    this.subtasksApi.patch(this.taskId(), sub.id, { done: !sub.done })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => {
          this.subtasks.update(s => s.map(x => x.id === updated.id ? updated : x));
          this.emitCounts();
        },
        error: () => this.toast.show('Failed to update subtask.', 'error'),
      });
  }

  deleteSubtask(sub: Subtask): void {
    this.pendingDeleteSubtask.set(sub);
  }

  confirmDeleteSubtask(): void {
    const sub = this.pendingDeleteSubtask();
    if (!sub) return;
    this.pendingDeleteSubtask.set(null);
    this.subtasksApi.delete(this.taskId(), sub.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.subtasks.update(s => s.filter(x => x.id !== sub.id));
          this.emitCounts();
        },
        error: () => this.toast.show('Failed to delete subtask.', 'error'),
      });
  }

  startEditSubtask(sub: Subtask): void {
    this.editingSubtaskId.set(sub.id);
    this.editingSubtaskTitle = sub.title;
  }

  confirmEditSubtask(sub: Subtask): void {
    const title = this.editingSubtaskTitle.trim();
    this.editingSubtaskId.set(null);
    if (!title || title === sub.title) return;
    this.subtasksApi.patch(this.taskId(), sub.id, { title })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => this.subtasks.update(s => s.map(x => x.id === updated.id ? updated : x)),
        error: () => this.toast.show('Failed to rename subtask.', 'error'),
      });
  }

  private emitCounts(): void {
    const subs = this.subtasks();
    this.subtaskCountChanged.emit({
      total: subs.length,
      done: subs.filter(s => s.done).length,
    });
  }
}
