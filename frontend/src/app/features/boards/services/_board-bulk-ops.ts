import { DestroyRef, WritableSignal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Task, TasksApiService } from '../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../shared/services/toast.service';

export function bulkMoveTasks(
  selectedTaskIds: WritableSignal<Set<number>>,
  bulkMoveTarget: WritableSignal<number | null>,
  tasks: WritableSignal<Task[]>,
  tasksApi: TasksApiService,
  toast: ToastService,
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
    next: () => toast.show(`Moved ${ids.length} task(s)`),
    error: () => {
      tasks.set(snapshot);
      toast.show('Failed to move tasks.', 'error');
    },
  });
}

export function bulkDeleteTasks(
  selectedTaskIds: WritableSignal<Set<number>>,
  pendingBulkDelete: WritableSignal<boolean>,
  tasks: WritableSignal<Task[]>,
  tasksApi: TasksApiService,
  toast: ToastService,
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
        toast.show(`Deleted ${ids.length} task(s)`);
      } else if (deletedIds.length === 0) {
        toast.show(`Failed to delete ${ids.length} task(s).`, 'error');
      } else {
        toast.show(`Deleted ${deletedIds.length}, failed ${failedIds.size} task(s).`, 'error');
      }
    });
}
