import { ChangeDetectionStrategy, Component, inject, signal, computed, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TranslateModule } from '@ngx-translate/core';
import { TasksApiService, Task } from '../../../../core/tasks/tasks-api.service';
import { ColumnsApiService, Column } from '../../../../core/columns/columns-api.service';
import { ActivityApiService, ActivityEntry } from '../../../../core/activity/activity-api.service';
import { PRIORITY_COLORS, BRAND_COLOR } from '../../../../shared/constants/colors';
import { initBoardPage } from '../../utils/board-page-init';

@Component({
  selector: 'app-board-timetravel-page',
  standalone: true,
  imports: [DatePipe, RouterModule, TranslateModule],
  templateUrl: './board-timetravel-page.component.html',
  styleUrl: './board-timetravel-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoardTimetravelPageComponent implements OnInit {
  protected readonly board = initBoardPage();
  private readonly tasksApi = inject(TasksApiService);
  private readonly columnsApi = inject(ColumnsApiService);
  private readonly activityApi = inject(ActivityApiService);
  loading = signal(true);
  allTasks = signal<Task[]>([]);
  columns = signal<Column[]>([]);
  activities = signal<ActivityEntry[]>([]);
  playing = signal(false);

  sliderValue = signal(100);
  private playInterval: ReturnType<typeof setInterval> | null = null;

  dateRange = computed(() => {
    const tasks = this.allTasks();
    if (tasks.length === 0) return { start: new Date(), end: new Date() };
    const dates = tasks.map(t => new Date(t.created_at).getTime());
    const start = new Date(Math.min(...dates));
    const end = new Date();
    return { start, end };
  });

  selectedDate = computed(() => {
    const { start, end } = this.dateRange();
    const range = end.getTime() - start.getTime();
    return new Date(start.getTime() + (this.sliderValue() / 100) * range);
  });

  formattedDate = computed(() => {
    const d = this.selectedDate();
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  });

  visibleTasks = computed(() => {
    const date = this.selectedDate().getTime();
    return this.allTasks().filter(t => {
      const created = new Date(t.created_at).getTime();
      if (created > date) return false;
      return true;
    });
  });

  tasksByColumn = computed(() => {
    const tasks = this.visibleTasks();
    const cols = this.columns();
    const map = new Map<number, Task[]>();
    for (const c of cols) map.set(c.id, []);

    for (const t of tasks) {
      if (t.column && map.has(t.column)) {
        map.get(t.column)!.push(t);
      }
    }
    return map;
  });

  stats = computed(() => {
    const visible = this.visibleTasks();
    const total = this.allTasks().length;
    return {
      visible: visible.length,
      total,
      percentage: total > 0 ? Math.round((visible.length / total) * 100) : 0,
    };
  });

  nearbyActivities = computed(() => {
    const date = this.selectedDate().getTime();
    const window = 24 * 60 * 60 * 1000;
    return this.activities()
      .filter(a => {
        const t = new Date(a.created_at).getTime();
        return Math.abs(t - date) <= window;
      })
      .slice(0, 10);
  });

  priorityColor(priority: string): string {
    return PRIORITY_COLORS[priority as keyof typeof PRIORITY_COLORS] ?? BRAND_COLOR;
  }

  ngOnInit(): void {
    forkJoin([
      this.tasksApi.getByBoard(this.board.boardId()),
      this.tasksApi.getArchive(this.board.boardId()),
      this.columnsApi.getByBoard(this.board.boardId()),
      this.activityApi.getByBoard(this.board.boardId()),
    ]).pipe(takeUntilDestroyed(this.board.destroyRef)).subscribe({
      next: ([tasks, archived, columns, activities]) => {
        this.allTasks.set([...tasks, ...archived]);
        this.columns.set(columns);
        this.activities.set(activities);
        this.loading.set(false);
      },
    });
  }

  onSliderChange(event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    this.sliderValue.set(value);
  }

  togglePlay(): void {
    if (this.playing()) {
      this.stopPlay();
    } else {
      this.startPlay();
    }
  }

  private startPlay(): void {
    if (this.sliderValue() >= 100) this.sliderValue.set(0);
    this.playing.set(true);
    this.playInterval = setInterval(() => {
      const next = this.sliderValue() + 0.5;
      if (next >= 100) {
        this.sliderValue.set(100);
        this.stopPlay();
      } else {
        this.sliderValue.set(next);
      }
    }, 50);
  }

  private stopPlay(): void {
    this.playing.set(false);
    if (this.playInterval) {
      clearInterval(this.playInterval);
      this.playInterval = null;
    }
  }
}
