import { ChangeDetectionStrategy, Component, inject, signal, computed, OnInit, ElementRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { initBoardPage } from '../../utils/board-page-init';
import {
  COLUMN_WIDTH,
  ROW_HEIGHT,
  ZoomLevel,
  buildDependencyLines,
  buildGanttBars,
  buildTimelineHeaders,
  computeDateRange,
  rowCenter,
  todayPosition,
} from './_gantt-layout';

@Component({
  selector: 'app-board-gantt-page',
  imports: [RouterModule, TranslateModule],
  templateUrl: './board-gantt-page.component.html',
  styleUrl: './board-gantt-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardGanttPageComponent implements OnInit {
  protected readonly board = initBoardPage();
  private readonly tasksApi = inject(TasksApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly toast = inject(ToastService);
  private readonly translate = inject(TranslateService);
  private readonly elRef = inject(ElementRef);
  protected readonly rowHeight = ROW_HEIGHT;
  private stopDrag: (() => void) | null = null;

  loading = signal(true);
  tasks = signal<Task[]>([]);
  columns = signal<Column[]>([]);
  zoom = signal<ZoomLevel>('week');
  selectedTask = signal<Task | null>(null);

  dragFromTaskId = signal<number | null>(null);
  dragLineEnd = signal<{ x: number; y: number } | null>(null);
  pendingDeleteDep = signal<{ taskId: number; depId: number; dependsOnTitle: string } | null>(null);

  private columnTitles = computed(() => new Map(this.columns().map(c => [c.id, c.title])));

  datedTasks = computed(() => this.tasks().filter(t => t.start_date || t.due_date));
  undatedTasks = computed(() => this.tasks().filter(t => !t.start_date && !t.due_date));
  dateRange = computed(() => computeDateRange(this.datedTasks()));
  timelineHeaders = computed(() => buildTimelineHeaders(this.dateRange().start, this.dateRange().days, this.zoom()));
  ganttBars = computed(() => buildGanttBars(this.datedTasks(), this.dateRange(), this.columnTitles()));
  todayPosition = computed(() => todayPosition(this.dateRange()));
  timelineWidth = computed(() => this.dateRange().days * COLUMN_WIDTH[this.zoom()]);
  dependencyLines = computed(() => buildDependencyLines(this.ganttBars(), this.timelineWidth()));

  dragLine = computed(() => {
    const fromId = this.dragFromTaskId();
    const end = this.dragLineEnd();
    if (fromId === null || !end) return null;
    const bars = this.ganttBars();
    const idx = bars.findIndex(b => b.task.id === fromId);
    if (idx < 0) return null;
    const bar = bars[idx];
    const x1 = (bar.left + bar.width) / 100 * this.timelineWidth();
    return { x1, y1: rowCenter(idx), x2: end.x, y2: end.y };
  });

  constructor() {
    this.board.destroyRef.onDestroy(() => this.stopDrag?.());
  }

  ngOnInit(): void {
    forkJoin([
      this.tasksApi.getByBoard(this.board.boardId()),
      this.columnsApi.getByBoard(this.board.boardId()),
    ]).pipe(takeUntilDestroyed(this.board.destroyRef)).subscribe({
      next: ([tasks, columns]) => {
        this.tasks.set(tasks);
        this.columns.set(columns);
        this.loading.set(false);
      },
    });
  }

  setZoom(level: ZoomLevel): void {
    this.zoom.set(level);
  }

  selectTask(task: Task): void {
    this.selectedTask.set(this.selectedTask()?.id === task.id ? null : task);
  }

  onDragHandleDown(event: MouseEvent, taskId: number): void {
    event.stopPropagation();
    event.preventDefault();
    this.dragFromTaskId.set(taskId);

    const timelineBody = this.elRef.nativeElement.querySelector('.timeline-body') as HTMLElement;
    if (!timelineBody) return;

    const onMove = (e: MouseEvent) => {
      const rect = timelineBody.getBoundingClientRect();
      this.dragLineEnd.set({
        x: e.clientX - rect.left + timelineBody.scrollLeft,
        y: e.clientY - rect.top + timelineBody.scrollTop,
      });
    };

    const onUp = (e: MouseEvent) => {
      this.stopDrag?.();

      const targetEl = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement | null;
      const barEl = targetEl?.closest('[data-task-id]') as HTMLElement | null;
      const targetTaskId = barEl ? Number(barEl.dataset['taskId']) : null;

      if (targetTaskId && targetTaskId !== taskId) {
        this.createDependency(taskId, targetTaskId);
      }

      this.dragFromTaskId.set(null);
      this.dragLineEnd.set(null);
    };

    this.stopDrag?.();
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    // Listeners live on document, so they must also be removed if the page is destroyed mid-drag.
    this.stopDrag = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      this.stopDrag = null;
    };
  }

  onDepLineClick(taskId: number, depId: number, dependsOnTitle: string): void {
    this.pendingDeleteDep.set({ taskId, depId, dependsOnTitle });
  }

  confirmDeleteDep(): void {
    const dep = this.pendingDeleteDep();
    if (!dep) return;
    this.tasksApi.removeDependency(dep.taskId, dep.depId)
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: () => {
          this.tasks.update(tasks => tasks.map(t => {
            if (t.id !== dep.taskId) return t;
            return { ...t, dependencies: t.dependencies.filter(d => d.id !== dep.depId) };
          }));
          this.pendingDeleteDep.set(null);
          this.toast.show(this.translate.instant('TOAST.DEPENDENCY_REMOVED'));
        },
      });
  }

  cancelDeleteDep(): void {
    this.pendingDeleteDep.set(null);
  }

  private createDependency(taskId: number, dependsOnId: number): void {
    this.tasksApi.addDependency(taskId, dependsOnId)
      .pipe(takeUntilDestroyed(this.board.destroyRef))
      .subscribe({
        next: (dep) => {
          this.tasks.update(tasks => tasks.map(t => {
            if (t.id !== taskId) return t;
            if (t.dependencies.some(d => d.id === dep.id)) return t;
            return { ...t, dependencies: [...t.dependencies, dep] };
          }));
          this.toast.show(this.translate.instant('TOAST.DEPENDENCY_CREATED'));
        },
      });
  }
}
