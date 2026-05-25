import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal, computed, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TranslateModule } from '@ngx-translate/core';
import { BoardsApiService } from '../../../../core/boards/boards-api.service';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { PRIORITY_COLORS, BRAND_COLOR } from '../../../../shared/constants/colors';

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
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly boardsApi = inject(BoardsApiService);
  private readonly tasksApi = inject(TasksApiService);
  private readonly columnsApi = inject(ColumnsApiService);

  boardId = 0;
  boardTitle = signal('Board');
  loading = signal(true);
  tasks = signal<Task[]>([]);
  columns = signal<Column[]>([]);
  zoom = signal<ZoomLevel>('week');
  selectedTask = signal<Task | null>(null);

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

    const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];
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

  ngOnInit(): void {
    this.boardId = Number(this.route.snapshot.paramMap.get('id'));
    this.boardsApi.getById(this.boardId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(b => this.boardTitle.set(b.title));

    forkJoin([
      this.tasksApi.getByBoard(this.boardId),
      this.columnsApi.getByBoard(this.boardId),
    ]).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(([tasks, columns]) => {
      this.tasks.set(tasks);
      this.columns.set(columns);
      this.loading.set(false);
    });
  }

  setZoom(level: ZoomLevel): void {
    this.zoom.set(level);
  }

  selectTask(task: Task): void {
    this.selectedTask.set(this.selectedTask()?.id === task.id ? null : task);
  }

  private formatDate(d: Date, level: ZoomLevel): string {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    if (level === 'day') return `${d.getDate()} ${months[d.getMonth()]}`;
    if (level === 'week') return `${d.getDate()} ${months[d.getMonth()]}`;
    return `${months[d.getMonth()]} ${d.getFullYear()}`;
  }
}
