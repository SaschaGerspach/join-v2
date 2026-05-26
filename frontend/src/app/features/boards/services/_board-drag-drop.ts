import { DestroyRef, WritableSignal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { forkJoin } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { Column, ColumnsApiService } from '../../../core/columns/columns-api.service';
import { Task, TasksApiService } from '../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../shared/services/toast.service';

const ORDER_GAP = 1024;

function computeOrder(siblings: Task[], insertIndex: number): number {
  const prev = insertIndex > 0 ? siblings[insertIndex - 1]?.order : undefined;
  const next = siblings[insertIndex]?.order;

  if (prev === undefined && next === undefined) return 0;
  if (prev === undefined) return next! - ORDER_GAP;
  if (next === undefined) return prev + ORDER_GAP;
  return (prev + next) / 2;
}

export function handleColumnDrop(
  columns: WritableSignal<Column[]>,
  columnsApi: ColumnsApiService,
  toast: ToastService,
  translate: TranslateService,
  destroyRef: DestroyRef,
  event: CdkDragDrop<Column[]>,
): void {
  if (event.previousIndex === event.currentIndex) return;
  const snapshot = columns();
  const reordered = [...snapshot];
  const [moved] = reordered.splice(event.previousIndex, 1);
  reordered.splice(event.currentIndex, 0, moved);
  const updated = reordered.map((c, i) => ({ ...c, order: i }));
  columns.set(updated);

  forkJoin(updated.map(col => columnsApi.patch(col.id, { order: col.order })))
    .pipe(takeUntilDestroyed(destroyRef))
    .subscribe({
      error: () => {
        columns.set(snapshot);
        toast.show(translate.instant('TOAST.FAILED_REORDER_COLUMNS'), 'error');
      },
    });
}

export function handleTaskDrop(
  tasks: WritableSignal<Task[]>,
  filteredForColumn: (columnId: number) => Task[],
  tasksApi: TasksApiService,
  toast: ToastService,
  translate: TranslateService,
  destroyRef: DestroyRef,
  event: CdkDragDrop<Task[]>,
  targetColumnId: number,
): void {
  const task: Task = event.item.data;
  const isSameColumn = event.previousContainer === event.container;
  const snapshot = tasks();

  const targetTasks = filteredForColumn(targetColumnId).filter(t => t.id !== task.id);
  const newOrder = computeOrder(targetTasks, event.currentIndex);
  const movedTask = { ...task, order: newOrder, column: targetColumnId };

  tasks.update(list =>
    list.map(t => t.id === task.id ? movedTask : t)
  );

  tasksApi.reorder([{ id: task.id, order: newOrder, column: targetColumnId }])
    .pipe(takeUntilDestroyed(destroyRef))
    .subscribe({
      error: () => {
        tasks.set(snapshot);
        toast.show(
          translate.instant(isSameColumn ? 'TOAST.FAILED_REORDER_TASKS' : 'TOAST.FAILED_MOVE_TASK'),
          'error',
        );
      },
    });
}
