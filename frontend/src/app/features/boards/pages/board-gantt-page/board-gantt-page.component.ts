import { ChangeDetectionStrategy, Component, inject, signal, computed, OnInit, ElementRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { PRIORITY_COLORS, BRAND_COLOR } from '../../../../shared/constants/colors';
import { ToastService } from '../../../../shared/services/toast.service';
import { initBoardPage } from '../../utils/board-page-init';

type ZoomLevel = 'day' | 'week' | 'month';

type GanttBar = {
  task: Task;
  left: number;
  width: number;
  color: string;
  columnTitle: string;
};

@Component({
  selector: 'app-board-gantt-page',
  standalone: true,
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
  loading = signal(true);
  tasks = signal<Task[]>([]);
  columns = signal<Column[]>([]);
  zoom = signal<ZoomLevel>('week');
  selectedTask = signal<Task | null>(null);

  dragFromTaskId = signal<number | null>(null);
  dragLineEnd = signal<{ x: number; y: number } | null>(null);
  pendingDeleteDep = signal<{ taskId: number; depId: number; dependsOnTitle: string } | null>(null);

  private columnMap = computed(() => {
    const map = new Map<number, string>();
    for (const c of this.columns()) {
      map.set(c.id, c.title);
    }
    return map;
  });

  datedTasks = computed(() =>
    this.tasks().filter(t => t.start_date || t.due_date)
  );

  undatedTasks = computed(() =>
    this.tasks().filter(t => !t.start_date && !t.due_date)
  );

  dateRange = computed(() => {
    const dated = this.datedTasks();
    if (dated.length === 0) return { start: new Date(), end: new Date(), days: 0 };

    let min = Infinity;
    let max = -Infinity;
    for (const t of dated) {
      const s = t.start_date ? new Date(t.start_date).getTime() : null;
      const d = t.due_date ? new Date(t.due_date).getTime() : null;
      const earliest = s ?? d!;
      const latest = d ?? s!;
      if (earliest < min) min = earliest;
      if (latest > max) max = latest;
    }

    const start = new Date(min);
    start.setDate(start.getDate() - 7);
    const end = new Date(max);
    end.setDate(end.getDate() + 7);
    const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    return { start, end, days };
  });

  timelineHeaders = computed(() => {
    const { start, days } = this.dateRange();
    if (days === 0) return [];
    const z = this.zoom();
    const headers: { label: string; span: number }[] = [];

    if (z === 'day') {
      for (let i = 0; i < days; i++) {
        const d = new Date(start);
        d.setDate(d.getDate() + i);
        headers.push({ label: this.formatDate(d, 'day'), span: 1 });
      }
    } else if (z === 'week') {
      let i = 0;
      while (i < days) {
        const d = new Date(start);
        d.setDate(d.getDate() + i);
        const weekEnd = 7 - d.getDay();
        const span = Math.min(weekEnd || 7, days - i);
        headers.push({ label: this.formatDate(d, 'week'), span });
        i += span;
      }
    } else {
      let i = 0;
      while (i < days) {
        const d = new Date(start);
        d.setDate(d.getDate() + i);
        const daysInMonth = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
        const remaining = daysInMonth - d.getDate() + 1;
        const span = Math.min(remaining, days - i);
        headers.push({ label: this.formatDate(d, 'month'), span });
        i += span;
      }
    }
    return headers;
  });

  ganttBars = computed<GanttBar[]>(() => {
    const dated = this.datedTasks();
    const { start, days } = this.dateRange();
    if (days === 0) return [];
    const startMs = start.getTime();
    const totalMs = days * 24 * 60 * 60 * 1000;
    const colMap = this.columnMap();

    return dated.map(t => {
      const s = t.start_date ? new Date(t.start_date).getTime() : null;
      const d = t.due_date ? new Date(t.due_date + 'T23:59:59').getTime() : null;
      const barStart = s ?? d!;
      const barEnd = d ?? (s! + 24 * 60 * 60 * 1000);

      const left = ((barStart - startMs) / totalMs) * 100;
      const width = Math.max(((barEnd - barStart) / totalMs) * 100, 0.5);

      return {
        task: t,
        left,
        width,
        color: PRIORITY_COLORS[t.priority] ?? BRAND_COLOR,
        columnTitle: (t.column ? colMap.get(t.column) : null) ?? '',
      };
    });
  });

  todayPosition = computed(() => {
    const { start, days } = this.dateRange();
    if (days === 0) return -1;
    const now = new Date();
    const startMs = start.getTime();
    const totalMs = days * 24 * 60 * 60 * 1000;
    const pos = ((now.getTime() - startMs) / totalMs) * 100;
    return pos >= 0 && pos <= 100 ? pos : -1;
  });

  dependencyLines = computed(() => {
    const bars = this.ganttBars();
    const barMap = new Map<number, GanttBar>();
    for (const b of bars) barMap.set(b.task.id, b);
    const barIndex = new Map<number, number>();
    bars.forEach((b, i) => barIndex.set(b.task.id, i));

    const lines: { x1: number; y1: number; x2: number; y2: number; taskId: number; depId: number; dependsOnTitle: string }[] = [];
    for (const bar of bars) {
      for (const dep of bar.task.dependencies) {
        const source = barMap.get(dep.depends_on);
        if (!source) continue;
        const sourceIdx = barIndex.get(dep.depends_on)!;
        const targetIdx = barIndex.get(bar.task.id)!;
        lines.push({
          x1: source.left + source.width,
          y1: sourceIdx * 44 + 22,
          x2: bar.left,
          y2: targetIdx * 44 + 22,
          taskId: bar.task.id,
          depId: dep.id,
          dependsOnTitle: dep.title,
        });
      }
    }
    return lines;
  });

  colWidth = computed(() => {
    const z = this.zoom();
    if (z === 'day') return 40;
    if (z === 'week') return 20;
    return 8;
  });

  timelineWidth = computed(() => {
    return this.dateRange().days * this.colWidth();
  });

  dragLine = computed(() => {
    const fromId = this.dragFromTaskId();
    const end = this.dragLineEnd();
    if (fromId === null || !end) return null;
    const bars = this.ganttBars();
    const idx = bars.findIndex(b => b.task.id === fromId);
    if (idx < 0) return null;
    const bar = bars[idx];
    const tw = this.timelineWidth();
    const x1 = (bar.left + bar.width) / 100 * tw;
    const y1 = idx * 44 + 22;
    return { x1, y1, x2: end.x, y2: end.y };
  });

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
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);

      const targetEl = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement | null;
      const barEl = targetEl?.closest('[data-task-id]') as HTMLElement | null;
      const targetTaskId = barEl ? Number(barEl.dataset['taskId']) : null;

      if (targetTaskId && targetTaskId !== taskId) {
        this.createDependency(taskId, targetTaskId);
      }

      this.dragFromTaskId.set(null);
      this.dragLineEnd.set(null);
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
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

  private formatDate(d: Date, level: ZoomLevel): string {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    if (level === 'day') return `${d.getDate()} ${months[d.getMonth()]}`;
    if (level === 'week') return `${d.getDate()} ${months[d.getMonth()]}`;
    return `${months[d.getMonth()]} ${d.getFullYear()}`;
  }
}
