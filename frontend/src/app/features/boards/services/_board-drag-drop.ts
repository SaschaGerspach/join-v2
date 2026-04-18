import { DestroyRef, WritableSignal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { forkJoin } from 'rxjs';
import { Column, ColumnsApiService } from '../../../core/columns/columns-api.service';
import { Task, TasksApiService } from '../../../core/tasks/tasks-api.service';
import { ToastService } from '../../../shared/services/toast.service';

export function handleColumnDrop(
  columns: WritableSignal<Column[]>,
  columnsApi: ColumnsApiService,
  toast: ToastService,
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
        toast.show('Failed to reorder columns.', 'error');
      },
    });
}

export function handleTaskDrop(
  tasks: WritableSignal<Task[]>,
  filteredForColumn: (columnId: number) => Task[],
  tasksApi: TasksApiService,
  toast: ToastService,
  destroyRef: DestroyRef,
  event: CdkDragDrop<Task[]>,
  targetColumnId: number,
): void {
  const task: Task = event.item.data;
  const isSameColumn = event.previousContainer === event.container;
  const snapshot = tasks();

  if (isSameColumn) {
    const colTasks = filteredForColumn(targetColumnId);
    const reordered = [...colTasks];
    const [moved] = reordered.splice(event.previousIndex, 1);
    reordered.splice(event.currentIndex, 0, moved);
    const updated = reordered.map((t, i) => ({ ...t, order: i }));
    tasks.update(list =>
      list.map(t => updated.find(u => u.id === t.id) ?? t)
    );
    tasksApi.reorder(updated.map(t => ({ id: t.id, order: t.order, column: t.column })))
      .pipe(takeUntilDestroyed(destroyRef))
      .subscribe({
        error: () => {
          tasks.set(snapshot);
          toast.show('Failed to reorder tasks.', 'error');
        },
      });
  } else {
    const prevTasks = filteredForColumn(task.column!).filter(t => t.id !== task.id)
      .map((t, i) => ({ ...t, order: i }));
    const targetTasks = [...filteredForColumn(targetColumnId)];
    targetTasks.splice(event.currentIndex, 0, { ...task, column: targetColumnId });
    const updatedTarget = targetTasks.map((t, i) => ({ ...t, order: i, column: targetColumnId }));

    tasks.update(list =>
      list.map(t => {
        const inPrev = prevTasks.find(u => u.id === t.id);
        const inTarget = updatedTarget.find(u => u.id === t.id);
        return inTarget ?? inPrev ?? t;
      })
    );

    tasksApi.reorder([
      ...prevTasks.map(t => ({ id: t.id, order: t.order, column: t.column })),
      ...updatedTarget.map(t => ({ id: t.id, order: t.order, column: t.column })),
    ]).pipe(takeUntilDestroyed(destroyRef)).subscribe({
      error: () => {
        tasks.set(snapshot);
        toast.show('Failed to move task.', 'error');
      },
    });
  }
}
