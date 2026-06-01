import { ChangeDetectionStrategy, Component, DestroyRef, inject, input, output, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CdkDragDrop, DragDropModule } from '@angular/cdk/drag-drop';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { Subtask, SubtasksApiService } from '../../../../core/tasks/subtasks-api.service';
import { AiApiService, AI_FEATURE } from '../../../../core/ai/ai-api.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../shared/services/toast.service';

@Component({
  selector: 'app-task-subtasks',
  standalone: true,
  imports: [FormsModule, DragDropModule, TranslateModule, ConfirmDialogComponent],
  templateUrl: './task-subtasks.component.html',
  styleUrl: './task-subtasks.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskSubtasksComponent implements OnInit {
  private readonly subtasksApi = inject(SubtasksApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly destroyRef = inject(DestroyRef);
  readonly ai = inject(AiApiService);
  readonly aiFeature = AI_FEATURE;

  taskId = input.required<number>();
  taskTitle = input('');
  taskDescription = input('');

  subtaskCountChanged = output<{ total: number; done: number }>();

  subtasks = signal<Subtask[]>([]);
  newSubtaskTitle = signal('');
  editingSubtaskId = signal<number | null>(null);
  editingSubtaskTitle = signal('');
  pendingDeleteSubtask = signal<Subtask | null>(null);
  suggesting = signal(false);

  ngOnInit(): void {
    this.ai.ensureLoaded();
    this.subtasksApi.getByTask(this.taskId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: subs => this.subtasks.set(subs),
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_LOAD_SUBTASKS'), 'error'),
      });
  }

  suggestSubtasks(): void {
    const title = this.taskTitle().trim();
    if (!title || this.suggesting()) return;
    this.suggesting.set(true);
    this.ai.suggestSubtasks(title, this.taskDescription().trim() || undefined)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: titles => this.createSuggested(titles),
        error: () => this.suggesting.set(false),
      });
  }

  private createSuggested(titles: string[]): void {
    const fresh = titles.map(t => t.trim()).filter(Boolean);
    if (!fresh.length) {
      this.suggesting.set(false);
      return;
    }
    forkJoin(fresh.map(t => this.subtasksApi.create(this.taskId(), t)))
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: created => {
          this.subtasks.update(s => [...s, ...created]);
          this.emitCounts();
          this.suggesting.set(false);
        },
        error: () => {
          this.toast.show(this.translate.instant('TOAST.FAILED_ADD_SUBTASK'), 'error');
          this.suggesting.set(false);
        },
      });
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
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_ADD_SUBTASK'), 'error'),
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
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_UPDATE_SUBTASK'), 'error'),
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
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_DELETE_SUBTASK'), 'error'),
      });
  }

  startEditSubtask(sub: Subtask): void {
    this.editingSubtaskId.set(sub.id);
    this.editingSubtaskTitle.set(sub.title);
  }

  confirmEditSubtask(sub: Subtask): void {
    const title = this.editingSubtaskTitle().trim();
    this.editingSubtaskId.set(null);
    if (!title || title === sub.title) return;
    this.subtasksApi.patch(this.taskId(), sub.id, { title })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => this.subtasks.update(s => s.map(x => x.id === updated.id ? updated : x)),
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_RENAME_SUBTASK'), 'error'),
      });
  }

  dropSubtask(event: CdkDragDrop<Subtask[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    const reordered = [...this.subtasks()];
    const [moved] = reordered.splice(event.previousIndex, 1);
    reordered.splice(event.currentIndex, 0, moved);
    this.subtasks.set(reordered);
    this.subtasksApi.reorder(this.taskId(), reordered.map(s => s.id))
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        error: () => this.toast.show(this.translate.instant('TOAST.FAILED_REORDER_SUBTASKS'), 'error'),
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
