import { DestroyRef, WritableSignal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { TranslateService } from '@ngx-translate/core';
import { Task, TasksApiService } from '../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../shared/services/toast.service';

export function bulkMoveTasks(
  selectedTaskIds: WritableSignal<Set<number>>,
  bulkMoveTarget: WritableSignal<number | null>,
  tasks: WritableSignal<Task[]>,
  tasksApi: TasksApiService,
  toast: ToastService,
  translate: TranslateService,
  destroyRef: DestroyRef,
): void {
  const targetCol = bulkMoveTarget();
  if (targetCol === null) return;
  const ids = [...selectedTaskIds()];
  const items = ids.map((id, i) => ({ id, order: i, column: targetCol }));
  const snapshot = tasks();

  tasks.update(list =>
    list.map(t => ids.includes(t.id) ? { ...t, column: targetCol } : t)
  );
  selectedTaskIds.set(new Set());

  tasksApi.reorder(items).pipe(takeUntilDestroyed(destroyRef)).subscribe({
    next: () => toast.show(translate.instant('TOAST.MOVED_TASKS', { count: ids.length })),
    error: () => {
      tasks.set(snapshot);
      toast.show(translate.instant('TOAST.FAILED_MOVE_TASKS'), 'error');
    },
  });
}

export function bulkDeleteTasks(
  selectedTaskIds: WritableSignal<Set<number>>,
  pendingBulkDelete: WritableSignal<boolean>,
  tasks: WritableSignal<Task[]>,
  tasksApi: TasksApiService,
  toast: ToastService,
  translate: TranslateService,
  destroyRef: DestroyRef,
): void {
  const ids = [...selectedTaskIds()];
  pendingBulkDelete.set(false);
  if (ids.length === 0) return;

  forkJoin(ids.map((id, i) => tasksApi.delete(id).pipe(
    catchError(() => of({ failed: true, index: i })),
  )))
    .pipe(takeUntilDestroyed(destroyRef))
    .subscribe(results => {
      const failedIds = new Set(results.filter(r => r && typeof r === 'object' && 'failed' in r).map(r => ids[(r as { index: number }).index]));
      const deletedIds = ids.filter(id => !failedIds.has(id));
      if (deletedIds.length > 0) {
        tasks.update(t => t.filter(task => !deletedIds.includes(task.id)));
      }
      selectedTaskIds.set(new Set());
      if (failedIds.size === 0) {
        toast.show(translate.instant('TOAST.DELETED_TASKS', { count: ids.length }));
      } else if (deletedIds.length === 0) {
        toast.show(translate.instant('TOAST.FAILED_DELETE_TASKS', { count: ids.length }), 'error');
      } else {
        toast.show(translate.instant('TOAST.PARTIAL_DELETE_TASKS', { deleted: deletedIds.length, failed: failedIds.size }), 'error');
      }
    });
}
